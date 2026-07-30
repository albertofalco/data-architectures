"""Compare table checksums and inventories between two MySQL databases."""

# ==================== IMPORTS ====================

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine
from sqlalchemy.exc import SQLAlchemyError


# ==================== CONFIGURATION ====================

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

DEFAULT_PROD_DB = "data_arch_prod"
DEFAULT_TEST_DB = "data_arch_test"
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_$]+$")


# ==================== MAIN CLASSES ====================

@dataclass
class ChecksumResult:
    """Store checksum comparison results by outcome."""
    equal: dict[str, tuple[int | None, int | None]]
    different: dict[str, tuple[int | None, int | None]]
    errors: dict[str, str]
    only_in_prod: set[str]
    only_in_test: set[str]


# ==================== HELPER FUNCTIONS ====================

def parse_args() -> argparse.Namespace:
    """Parse command-line database selection arguments."""
    parser = argparse.ArgumentParser(
        description="Compara CHECKSUM TABLE entre dos bases MySQL."
    )
    parser.add_argument(
        "--prod-db",
        default=DEFAULT_PROD_DB,
        help=f"Base de datos origen/prod. Default: {DEFAULT_PROD_DB}",
    )
    parser.add_argument(
        "--test-db",
        default=DEFAULT_TEST_DB,
        help=f"Base de datos destino/test. Default: {DEFAULT_TEST_DB}",
    )
    return parser.parse_args()


def require_env(name: str) -> str:
    """Return a required environment variable."""
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Falta la variable de entorno requerida: {name}")
    return value


def create_mysql_engine() -> Engine:
    """Create a MySQL engine from environment variables."""
    host = require_env("DB_HOST")
    port = require_env("DB_PORT")
    user = require_env("DB_USER")
    password = require_env("DB_PASSWORD")

    try:
        port_number = int(port)
    except ValueError as exc:
        raise RuntimeError("DB_PORT debe ser un numero entero.") from exc

    url = URL.create(
        "mysql+mysqlconnector",
        username=user,
        password=password,
        host=host,
        port=port_number,
    )
    return create_engine(url)


def quote_identifier(identifier: str) -> str:
    """Validate and quote a MySQL identifier."""
    if not IDENTIFIER_RE.fullmatch(identifier):
        raise ValueError(f"Identificador MySQL no soportado: {identifier!r}")
    return f"`{identifier}`"


def get_tables(engine: Engine, db_name: str) -> set[str]:
    """Return the base tables in a MySQL database."""
    query = text(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = :db_name
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
    )

    with engine.connect() as conn:
        return {row[0] for row in conn.execute(query, {"db_name": db_name})}


def get_checksum(engine: Engine, db_name: str, table_name: str) -> int | None:
    """Return the MySQL checksum for a table."""
    qualified_table = (
        f"{quote_identifier(db_name)}.{quote_identifier(table_name)}"
    )
    query = text(f"CHECKSUM TABLE {qualified_table}")

    with engine.connect() as conn:
        result = conn.execute(query).fetchone()

    if result is None:
        raise RuntimeError("CHECKSUM TABLE no devolvio resultados.")

    return result[1]


def compare_databases(engine: Engine, prod_db: str, test_db: str) -> ChecksumResult:
    """Compare common table checksums and database inventories."""
    print(f"Obteniendo tablas de {prod_db}...")
    prod_tables = get_tables(engine, prod_db)
    print(f"Obteniendo tablas de {test_db}...")
    test_tables = get_tables(engine, test_db)

    only_in_prod = prod_tables - test_tables
    only_in_test = test_tables - prod_tables
    common_tables = sorted(prod_tables & test_tables)
    
    total_common = len(common_tables)
    print(f"Se encontraron {total_common} tablas comunes para comparar.")

    equal: dict[str, tuple[int | None, int | None]] = {}
    different: dict[str, tuple[int | None, int | None]] = {}
    errors: dict[str, str] = {}

    for i, table_name in enumerate(common_tables, start=1):
        print(f"Procesando tabla {table_name} ({i}/{total_common})...")
        try:
            prod_checksum = get_checksum(engine, prod_db, table_name)
            test_checksum = get_checksum(engine, test_db, table_name)
        except (SQLAlchemyError, RuntimeError, ValueError) as exc:
            errors[table_name] = str(exc)
            continue

        checksums = (prod_checksum, test_checksum)
        if prod_checksum == test_checksum:
            equal[table_name] = checksums
        else:
            different[table_name] = checksums

    return ChecksumResult(
        equal=equal,
        different=different,
        errors=errors,
        only_in_prod=only_in_prod,
        only_in_test=only_in_test,
    )


def print_report(result: ChecksumResult, prod_db: str, test_db: str) -> None:
    """Print a human-readable checksum comparison report."""
    compared = len(result.equal) + len(result.different)

    print(f"Comparacion de checksums: {prod_db} vs {test_db}")
    print(f"Tablas comparadas: {compared}")
    print(f"Iguales: {len(result.equal)}")
    print(f"Diferentes: {len(result.different)}")
    print(f"Solo en {prod_db}: {len(result.only_in_prod)}")
    print(f"Solo en {test_db}: {len(result.only_in_test)}")
    print(f"Errores: {len(result.errors)}")

    if result.different:
        print("\nHASHES DIFERENTES")
        for table_name, (prod_checksum, test_checksum) in sorted(
            result.different.items()
        ):
            print(
                f"- {table_name}: {prod_db}={prod_checksum}, "
                f"{test_db}={test_checksum}"
            )

    if result.only_in_prod:
        print(f"\nTABLAS SOLO EN {prod_db}")
        for table_name in sorted(result.only_in_prod):
            print(f"- {table_name}")

    if result.only_in_test:
        print(f"\nTABLAS SOLO EN {test_db}")
        for table_name in sorted(result.only_in_test):
            print(f"- {table_name}")

    if result.errors:
        print("\nERRORES")
        for table_name, error in sorted(result.errors.items()):
            print(f"- {table_name}: {error}")


def has_failures(result: ChecksumResult) -> bool:
    """Return whether the comparison contains any failure."""
    return bool(
        result.different
        or result.only_in_prod
        or result.only_in_test
        or result.errors
    )


# ==================== MAIN FUNCTIONS ====================

def main() -> int:
    """Run the checksum comparison and return its exit status."""
    args = parse_args()

    try:
        engine = create_mysql_engine()
        result = compare_databases(engine, args.prod_db, args.test_db)
    except (RuntimeError, SQLAlchemyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print_report(result, args.prod_db, args.test_db)
    return 1 if has_failures(result) else 0


# ==================== EXECUTION ====================

if __name__ == "__main__":
    sys.exit(main())
