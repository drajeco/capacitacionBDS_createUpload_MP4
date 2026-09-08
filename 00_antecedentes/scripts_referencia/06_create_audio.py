import os
import asyncio
import edge_tts

# Directorios de entrada y salida
fld_textFolder = os.path.join(os.getcwd(), "05_txt_es")
fld_audioFolder = os.path.join(os.getcwd(), "06_audio")

# Crear carpeta de audio si no existe
os.makedirs(fld_audioFolder, exist_ok=True)

# Filtrar únicamente los archivos .txt de la carpeta
l_textFiles = [f for f in os.listdir(fld_textFolder) if f.endswith(".txt")]

async def generar_audio_individual(archivo_txt, voz="es-UY-ValentinaNeural"):
    text_path = os.path.join(fld_textFolder, archivo_txt)
    audio_file = archivo_txt.removesuffix(".txt") + ".mp3" # Se usa .mp3 por compatibilidad nativa
    audio_path = os.path.join(fld_audioFolder, audio_file)

    with open(text_path, "r", encoding="utf-8") as f:
        texto = f.read()

    communicate = edge_tts.Communicate(texto, voz)
    await communicate.save(audio_path)
    print(f"¡Audio generado con éxito: {audio_file}!")

async def procesar_lote_archivos():
    # Crear una lista de tareas asíncronas para todos los archivos
    tareas = [generar_audio_individual(archivo) for archivo in l_textFiles]
    
    # Ejecutar todas las tareas en paralelo
    await asyncio.gather(*tareas)

# Ejecución directa en Jupyter Notebook
if __name__ == "__main__":
    asyncio.run(procesar_lote_archivos())
