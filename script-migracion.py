import pandas as pd
import psycopg2
from psycopg2 import Error
from datetime import datetime

def conectar_bd():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            dbname="conacyth-becarios",
            user="postgres",
            password="12345",
            connect_timeout=10,
            sslmode="prefer"
        )
        return conn
    except Error as e:
        print(f"Error conectando a PostgreSQL: {e}")
        return None

def cargar_datos_excel():
    try:
        df = pd.read_excel('excel-becarios.xlsx', nrows=906354)
        df['INSTITUCIÓN'] = df['INSTITUCIÓN'].fillna('BECA NACIONAL')
        return df
    except Exception as e:
        print(f"Error cargando el archivo Excel: {e}")
        return None

def convertir_fecha(fecha):
    try:
        if pd.isna(fecha):
            return None
        if isinstance(fecha, pd.Timestamp):
            return fecha.date()
        elif isinstance(fecha, str):
            return datetime.strptime(fecha, '%d/%m/%Y').date()
        else:
            print(f"Formato de fecha no reconocido: {fecha}, tipo: {type(fecha)}")
            return None
    except Exception as e:
        print(f"Error convirtiendo fecha {fecha}: {e}")
        return None

def obtener_o_insertar_id(cur, tabla, campo_nombre, valor, campo_adicional=None, valor_adicional=None):
    try:
        # Mapeo de nombres de columnas actualizado
        mapeo_columnas = {
            'nivel_estudio': 'nombre_nivel',  # Corregido aquí
            'area_sni': 'nombre_area_sni',
            'estado': 'nombre_estado',
            'institucion': 'nombre_institucion',
            'programa': 'nombre_programa',
            'beca': 'nombre_beca'
        }
        
        # Obtener el nombre correcto de la columna
        nombre_columna = mapeo_columnas.get(tabla, campo_nombre)
        
        # Construir la consulta SELECT básica
        query = f"SELECT id_{tabla} FROM {tabla} WHERE {nombre_columna} = %s"
        params = [valor]
        
        # Añadir campo adicional si existe
        if campo_adicional and valor_adicional is not None:
            query += f" AND {campo_adicional} = %s"
            params.append(valor_adicional)
        
        # Intentar obtener el ID existente
        cur.execute(query, params)
        resultado = cur.fetchone()
        
        if resultado:
            return resultado[0]
        
        # Si no existe, insertar nuevo registro
        if campo_adicional and valor_adicional is not None:
            cur.execute(f"""
                INSERT INTO {tabla} ({nombre_columna}, {campo_adicional})
                VALUES (%s, %s)
                ON CONFLICT ({nombre_columna}, {campo_adicional}) DO UPDATE
                SET {nombre_columna} = EXCLUDED.{nombre_columna}
                RETURNING id_{tabla}
            """, (valor, valor_adicional))
        else:
            cur.execute(f"""
                INSERT INTO {tabla} ({nombre_columna})
                VALUES (%s)
                ON CONFLICT ({nombre_columna}) DO UPDATE
                SET {nombre_columna} = EXCLUDED.{nombre_columna}
                RETURNING id_{tabla}
            """, (valor,))
        
        return cur.fetchone()[0]
    except Exception as e:
        print(f"Error en obtener_o_insertar_id para {tabla}: {e}")
        raise

def crear_indices_unicos(conn):
    try:
        cur = conn.cursor()
        indices = [
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_area_sni_nombre ON area_sni(nombre_area_sni);",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_estado_nombre ON estado(nombre_estado);",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_nivel_estudio_nombre ON nivel_estudio(nombre_nivel);",  # Corregido aquí
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_institucion_nombre ON institucion(nombre_institucion);",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_programa_nombre_inst ON programa(nombre_programa, id_institucion);",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_beca_nombre ON beca(nombre_beca);"
        ]
        
        for indice in indices:
            try:
                cur.execute(indice)
            except Exception as e:
                print(f"Aviso al crear índice: {e}")
                continue
        
        conn.commit()
    except Exception as e:
        print(f"Error creando índices: {e}")
        conn.rollback()
    finally:
        cur.close()

def insertar_datos_base(conn, df):
    try:
        cur = conn.cursor()
        
        # Crear índices únicos necesarios
        crear_indices_unicos(conn)
        
        # Procesar cada registro
        for index, row in df.iterrows():
            try:
                # Obtener IDs de las tablas de catálogo
                id_area = obtener_o_insertar_id(cur, 'area_sni', 'nombre_area_sni', row['ÁREA DEL CONOCIMIENTO'])
                id_estado = obtener_o_insertar_id(cur, 'estado', 'nombre_estado', row['ENTIDAD'])
                id_nivel = obtener_o_insertar_id(cur, 'nivel_estudio', 'nombre_nivel', row['NIVEL DE ESTUDIOS'])
                id_institucion = obtener_o_insertar_id(cur, 'institucion', 'nombre_institucion', row['INSTITUCIÓN'])
                id_programa = obtener_o_insertar_id(cur, 'programa', 'nombre_programa', row['PROGRAMA DE ESTUDIOS'], 
                                                  'id_institucion', id_institucion)
                id_beca = obtener_o_insertar_id(cur, 'beca', 'nombre_beca', row['CONVOCATORIA'])
                
                # Procesar nombre y apellido del becario
                nombre_completo = row['NOMBRE BECARIO'].strip()
                nombre_parts = nombre_completo.split(' ', 1)
                nombre = nombre_parts[0]
                apellido = nombre_parts[1] if len(nombre_parts) > 1 else ''
                
                # Insertar becario
                cur.execute("""
                    INSERT INTO becario (nombre, apellido, id_estado, id_nivel_estudio, id_area_sni)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id_becario
                """, (nombre, apellido, id_estado, id_nivel, id_area))
                
                id_becario = cur.fetchone()[0]
                
                # Insertar relación becario_beca
                fecha_inicio = convertir_fecha(row['INICIO DE BECA'])
                fecha_fin = convertir_fecha(row['FIN DE BECA'])
                
                if fecha_inicio and fecha_fin:
                    cur.execute("""
                        INSERT INTO becario_beca (id_becario, id_beca, fecha_inicio, fecha_fin)
                        VALUES (%s, %s, %s, %s)
                    """, (id_becario, id_beca, fecha_inicio, fecha_fin))
                
                # Insertar montos de beca
                montos = [
                    row['IMPORTE PAGADO ENERO-MARZO'],
                    row['IMPORTE PAGADO ABRIL-JUNIO'],
                    row['IMPORTE PAGADO JULIO-SEPTIEMBRE'],
                    row['IMPORTE PAGADO OCTUBRE-DICIEMBRE']
                ]
                
                for monto in montos:
                    if pd.notna(monto) and monto != 0:
                        cur.execute("""
                            INSERT INTO montos_beca (monto, id_beca)
                            VALUES (%s, %s)
                        """, (monto, id_beca))
                
                # Insertar relación becario_institucion_programa
                cur.execute("""
                    INSERT INTO becario_institucion_programa (id_becario, id_institucion, id_programa)
                    VALUES (%s, %s, %s)
                """, (id_becario, id_institucion, id_programa))
                
                # Hacer commit después de cada registro exitoso
                conn.commit()
                print(f"Registro {index + 1} insertado exitosamente")
                
            except Exception as e:
                conn.rollback()
                print(f"Error procesando registro {index + 1}: {e}")
                continue
        
        print("Migración completada")
        
    except Exception as e:
        conn.rollback()
        print(f"Error durante la migración: {e}")
    finally:
        cur.close()

def main():
    conn = conectar_bd()
    if not conn:
        return
    
    df = cargar_datos_excel()
    if df is None:
        conn.close()
        return
    
    insertar_datos_base(conn, df)
    conn.close()

if __name__ == "__main__":
    main()