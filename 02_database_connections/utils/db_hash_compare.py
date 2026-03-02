"""
Script para comparar checksums de tablas entre bases de datos MySQL.

Compara los hashes de tablas específicas entre las bases de datos de producción
y test, ejecutando la consulta CHECKSUM TABLE directamente en el servidor MySQL.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')

DATABASES = {
    "prod": "data_arch_prod",
    "test": "data_arch_test"
}

TABLES = ["application_train", 
          "bureau", 
          "bureau_balance", 
          "credit_card_balance", 
          "dim_channel_type", 
          "dim_code_gender", 
          "dim_code_reject_reason", 
          "dim_credit_active", 
          "dim_credit_currency", 
          "dim_credit_type", 
          "dim_emergencystate_mode", 
          "dim_flag_last_appl_per_contract", 
          "dim_flag_own_car", 
          "dim_flag_own_realty", 
          "dim_fondkapremont_mode", 
          "dim_housetype_mode", 
          "dim_name_cash_loan_purpose", 
          "dim_name_client_type", 
          "dim_name_contract_status", 
          "dim_name_contract_type", 
          "dim_name_education_type", 
          "dim_name_family_status", 
          "dim_name_goods_category", 
          "dim_name_housing_type", 
          "dim_name_income_type", 
          "dim_name_payment_type", 
          "dim_name_portfolio", 
          "dim_name_product_type", 
          "dim_name_seller_industry", 
          "dim_name_type_suite", 
          "dim_name_yield_group", 
          "dim_occupation_type", 
          "dim_organization_type", 
          "dim_organization_type_2", 
          "dim_product_combination", 
          "dim_status", 
          "dim_wallsmaterial_mode", 
          "dim_weekday_appr_process_start", 
          "installments_payments", 
          "pos_cash_balance", 
          "previous_application"
]

def get_checksums(db_name: str, tables: list) -> dict:
    """Obtiene los checksums de las tablas especificadas en una base de datos."""
    engine = create_engine(
        f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{db_name}"
    )
    
    hashes = {}
    with engine.connect() as conn:
        for table in tables:
            stmt = text(f"CHECKSUM TABLE {table}")
            result = conn.execute(stmt).fetchone()
            checksum = result[1]
            hashes[table] = checksum
    
    return hashes

def compare_hashes(hashes_prod: dict, hashes_test: dict):
    """Compara los hashes de producción y test e imprime el resultado."""
    for table in TABLES:
        checksum_prod = hashes_prod.get(table)
        checksum_test = hashes_test.get(table)
        
        if checksum_prod == checksum_test:
            print(f"{table}: HASHES IGUALES - prod: {checksum_prod}, test: {checksum_test}")
        else:
            print(f"{table}: HASHES DIFERENTES - prod: {checksum_prod}, test: {checksum_test}")

def main():
    """Ejecuta el proceso de comparación de hashes entre entornos."""
    hashes_prod = get_checksums(DATABASES["prod"], TABLES)
    hashes_test = get_checksums(DATABASES["test"], TABLES)
    
    compare_hashes(hashes_prod, hashes_test)

if __name__ == '__main__':
    main()
