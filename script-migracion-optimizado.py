import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import numpy as np

def conectar_bd():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            dbname="becarios-final",
            user="postgres",
            password="12345",
            connect_timeout=10,
            sslmode="prefer"
        )
        return conn
    except Exception as e:
        print(f"Error conectando a PostgreSQL: {e}")
        return None

def cargar_datos_excel():
    try:
        # Usar chunksize para cargar el Excel en partes
        return pd.read_excel('excel-becarios.xlsx', nrows=5000)
    except Exception as e:
        print(f"Error cargando el archivo Excel: {e}")
        return None

def insertar_catalogo(cur, tabla, columna, valores):
    # Insertar valores únicos y obtener sus IDs
    valores_unicos = list(set(valores))
    query = f"""
        INSERT INTO {tabla} ({columna})
        VALUES (%s)
        ON CONFLICT ({columna}) DO UPDATE
        SET {columna} = EXCLUDED.{columna}
        RETURNING id_{tabla}, {columna}
    """
    
    resultados = {}
    for valor in valores_unicos:
        if pd.notna(valor):  # Solo procesar valores no-NaN
            # Convertir a string si es necesario
            valor_str = str(valor) if not isinstance(valor, str) else valor
            cur.execute(query, (valor_str,))
            id_valor, nombre = cur.fetchone()
            resultados[nombre] = id_valor
    
    return resultados

def procesar_lote(conn, df_chunk):
    try:
        cur = conn.cursor()
        
        # Insertar catálogos y obtener mapeos
        areas_sni = insertar_catalogo(cur, 'area_sni', 'nombre_area_sni', df_chunk['ÁREA DEL CONOCIMIENTO'])
        estados = insertar_catalogo(cur, 'estado', 'nombre_estado', df_chunk['ENTIDAD'])
        niveles = insertar_catalogo(cur, 'nivel_estudio', 'nombre_nivel', df_chunk['NIVEL DE ESTUDIOS'])
        instituciones = insertar_catalogo(cur, 'institucion', 'nombre_institucion', df_chunk['INSTITUCIÓN'].fillna('BECA NACIONAL'))
        becas = insertar_catalogo(cur, 'beca', 'nombre_beca', df_chunk['CONVOCATORIA'])
        
        # Preparar datos para inserción masiva
        datos_becarios = []
        datos_becario_beca = []
        datos_montos = []
        datos_programa = []
        datos_becario_programa = []
        
        for _, row in df_chunk.iterrows():
            # Procesar programa
            nombre_programa = row['PROGRAMA DE ESTUDIOS']
            id_institucion = instituciones[row['INSTITUCIÓN']]
            
            cur.execute("""
                INSERT INTO programa (nombre_programa, id_institucion)
                VALUES (%s, %s)
                ON CONFLICT (nombre_programa, id_institucion) DO UPDATE
                SET nombre_programa = EXCLUDED.nombre_programa
                RETURNING id_programa
            """, (nombre_programa, id_institucion))
            id_programa = cur.fetchone()[0]
            
            # Preparar datos del becario
            nombre_completo = row['NOMBRE BECARIO'].strip()
            nombre_parts = nombre_completo.split(' ', 1)
            nombre = nombre_parts[0]
            apellido = nombre_parts[1] if len(nombre_parts) > 1 else ''
            
            # Insertar becario
            cur.execute("""
                INSERT INTO becario (nombre, apellido, id_estado, id_nivel_estudio, id_area_sni)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_becario
            """, (
                nombre,
                apellido,
                estados[row['ENTIDAD']],
                niveles[row['NIVEL DE ESTUDIOS']],
                areas_sni[row['ÁREA DEL CONOCIMIENTO']]
            ))
            id_becario = cur.fetchone()[0]
            
            # Preparar datos para becario_beca
            fecha_inicio = pd.to_datetime(row['INICIO DE BECA']).date() if pd.notna(row['INICIO DE BECA']) else None
            fecha_fin = pd.to_datetime(row['FIN DE BECA']).date() if pd.notna(row['FIN DE BECA']) else None
            
            if fecha_inicio and fecha_fin:
                datos_becario_beca.append((id_becario, becas[row['CONVOCATORIA']], fecha_inicio, fecha_fin))
            
            # Preparar datos para montos_beca
            montos = [
                row['IMPORTE PAGADO ENERO-MARZO'],
                row['IMPORTE PAGADO ABRIL-JUNIO'],
                row['IMPORTE PAGADO JULIO-SEPTIEMBRE'],
                row['IMPORTE PAGADO OCTUBRE-DICIEMBRE']
            ]
            
            for monto in montos:
                if pd.notna(monto) and monto != 0:
                    datos_montos.append((float(monto), becas[row['CONVOCATORIA']]))
            
            # Preparar datos para becario_institucion_programa
            datos_becario_programa.append((id_becario, id_institucion, id_programa))
        
        # Insertar datos en lote
        if datos_becario_beca:
            execute_values(
                cur,
                "INSERT INTO becario_beca (id_becario, id_beca, fecha_inicio, fecha_fin) VALUES %s",
                datos_becario_beca
            )
        
        if datos_montos:
            execute_values(
                cur,
                "INSERT INTO montos_beca (monto, id_beca) VALUES %s",
                datos_montos
            )
        
        if datos_becario_programa:
            execute_values(
                cur,
                "INSERT INTO becario_institucion_programa (id_becario, id_institucion, id_programa) VALUES %s",
                datos_becario_programa
            )
        
        conn.commit()
        print(f"Lote de {len(df_chunk)} registros procesado exitosamente")
        
    except Exception as e:
        conn.rollback()
        print(f"Error procesando lote: {e}")
    finally:
        cur.close()

def main():
    conn = conectar_bd()
    if not conn:
        return
    
    try:
        # Cargar datos
        df = cargar_datos_excel()
        if df is None:
            return
        
        # Procesar en lotes de 1000 registros
        for i in range(0, len(df), 1000):
            df_chunk = df.iloc[i:i + 1000]
            procesar_lote(conn, df_chunk)
            print(f"Progreso: {min(i + 1000, len(df))}/{len(df)} registros")
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()