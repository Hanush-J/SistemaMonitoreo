import mysql.connector
from mysql.connector import Error

def probar_conexion():
    try:
        
        conexion = mysql.connector.connect(
            host='192.168.68.105',  
            user='joshua',  
            password='password',
            database='sistema_monitoreo' 
        )

        if conexion.is_connected():
            db_info = conexion.get_server_info()
            print("\n=======================================================")
            print("✅ ¡CONEXIÓN EXITOSA AL SERVIDOR UBUNTU!")
            print(f"✅ Versión del servidor MySQL remoto: {db_info}")
            print("✅ Base de datos 'sistema_monitoreo' lista para recibir datos.")
            print("=======================================================\n")
            
    except Error as e:
        print("\n=======================================================")
        print("❌ ERROR DE CONEXIÓN")
        print(f"Detalle: {e}")
        print("=======================================================\n")
    finally:
        # Siempre es buena práctica cerrar la conexión al terminar la prueba
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()
            print("🔌 Conexión cerrada correctamente.\n")

if __name__ == '__main__':
    probar_conexion()