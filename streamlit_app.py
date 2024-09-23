import streamlit as st
import pandas as pd
import requests
import io
import urllib3
import json

# Deshabilitar advertencias de verificación SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de la página
st.set_page_config(page_title="Visualizador de Datasets", page_icon=":bar_chart:", layout="wide")

def obtener_datasets_pagina(page):
    params = {
        '_page': page
    }
    try:
        response = requests.get('https://datos.gob.es/apidata/catalog/dataset.json', params=params)
        response.raise_for_status()
        data = response.json()
        datasets = data['result']['items']
        total_items = data['result'].get('totalItems', None)
        return datasets, total_items
    except requests.exceptions.HTTPError as errh:
        st.write(f"Error HTTP: {errh}")
    except requests.exceptions.RequestException as err:
        st.write(f"Error al obtener datasets: {err}")
    return [], None

@st.cache_data
def cargar_datos(url, formato):
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '').lower()
        data = response.content.decode('utf-8', errors='replace')
        
        st.markdown("**<span style='color:white;'>Content-Type:</span>**", unsafe_allow_html=True)
        st.write("El Content-Type es un encabezado HTTP que indica el tipo de contenido que devuelve la URL.")
        st.markdown(f"**<span style='color:white;'>URL de descarga:</span>** {url}", unsafe_allow_html=True)
        
        st.write("Contenido recibido (primeros 500 caracteres):")
        st.code(data[:500])
        
        if 'text/html' in content_type or data.strip().startswith('<!DOCTYPE html>'):
            st.write("La URL devuelve contenido HTML, no un archivo de datos.")
            return None
        
        if 'xml' in formato or 'xml' in content_type:
            if not data.strip().startswith('<'):
                st.write("El contenido recibido no es XML válido.")
                return None
            try:
                df = pd.read_xml(io.StringIO(data))
                return df
            except Exception as e:
                st.write(f"Error al cargar XML: {e}")
                return None
        elif 'csv' in formato or 'csv' in content_type:
            df = pd.read_csv(io.StringIO(data), sep=None, engine='python')
            return df
        elif 'json' in formato or 'json' in content_type:
            try:
                json_data = json.loads(data)
                if isinstance(json_data, dict):
                    df = pd.json_normalize(json_data)
                elif isinstance(json_data, list):
                    df = pd.DataFrame(json_data)
                else:
                    st.write("Formato JSON no reconocido.")
                    return None
                return df
            except json.JSONDecodeError as e:
                st.write(f"Error al cargar JSON: {e}")
                return None
        elif 'excel' in formato or 'spreadsheetml' in formato:
            df = pd.read_excel(io.BytesIO(response.content))
            return df
        else:
            st.write(f"Formato {formato} no soportado o contenido no válido.")
            return None
    except Exception as e:
        st.write(f"Error al cargar los datos: {e}")
        return None

def obtener_titulo(dataset):
    titulo = 'Sin título'
    title_field = dataset.get('title', [])
    if isinstance(title_field, list):
        for item in title_field:
            if item.get('_lang') == 'es':
                titulo = item.get('_value', 'Sin título')
                break
        else:
            if len(title_field) > 0:
                titulo = title_field[0].get('_value', 'Sin título')
    elif isinstance(title_field, dict):
        titulo = title_field.get('es', 'Sin título')
    elif isinstance(title_field, str):
        titulo = title_field
    return titulo

def main():
    # Inyectar CSS personalizado
    st.markdown("""
        <style>
        /* Importar la fuente IBM Plex Sans */
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans&display=swap');

        /* Cambiar el color de fondo de toda la aplicación */
        .stApp {
            background-color: #4C2F26;
            padding-bottom: 70px;
        }
        /* Cambiar el color del texto para garantizar legibilidad */
        html, body, [class*="css"]  {
            color: white;
            font-family: 'IBM Plex Sans', sans-serif;
        }
        /* Estilos para inputs y selects */
        input, select, textarea {
            background-color: #FFFFFF !important;
            color: #4C2F26 !important;
            font-family: 'IBM Plex Sans', sans-serif;
        }
        /* Estilos para las etiquetas */
        label {
            color: white;
            font-family: 'IBM Plex Sans', sans-serif;
        }
        /* Estilos para los botones */
        .stButton>button {
            background-color: #FFD100;
            color: #4C2F26;
            font-family: 'IBM Plex Sans', sans-serif;
        }
        /* Estilos para el pie de página */
        footer {
            position: fixed;
            bottom: 0;
            width: 100%;
            background-color: #4C2F26;
            color: white !important;
            text-align: center !important;
            padding: 10px;
            font-family: 'IBM Plex Sans', sans-serif;
        }
        footer a {
            color: white !important;
            text-decoration: none;
        }
        /* Asegurar que el título se muestre en blanco */
        .hero h1 {
            color: white !important;
            font-family: 'IBM Plex Sans', sans-serif;
        }
        /* Cambiar el color del texto y fondo del título del expander */
        .streamlit-expanderHeader {
            background-color: green !important;
            color: white !important;
            font-family: 'IBM Plex Sans', sans-serif;
        }
        /* Cambiar la fuente del contenido del expander */
        .streamlit-expanderContent {
            font-family: 'IBM Plex Sans', sans-serif;
        }
        </style>
    """, unsafe_allow_html=True)

    # Encabezado de la aplicación
    st.markdown("""
        <div class="hero">
            <h1>Visualizador de Datasets de Datos.gob.es</h1>
        </div>
    """, unsafe_allow_html=True)

    st.warning("La verificación SSL está deshabilitada. Esto puede exponer la aplicación a riesgos de seguridad.")

    if 'page' not in st.session_state:
        st.session_state.page = 0

    datasets, total_items = obtener_datasets_pagina(st.session_state.page)

    # Definir funciones de callback para los botones
    def previous_page():
        st.session_state.page -= 1

    def next_page():
        st.session_state.page += 1

    if datasets:
        opciones = []
        for dataset in datasets:
            titulo = obtener_titulo(dataset)
            distribuciones = dataset.get('distribution', [])
            for distribucion in distribuciones:
                url_descarga = distribucion.get('accessURL', '')
                formato = distribucion.get('format', {}).get('value', '').lower()
                opciones.append({'titulo': titulo, 'url': url_descarga, 'formato': formato})
                break  # Si solo deseas la primera distribución
        if opciones:
            st.markdown("""
                <style>
                .section-header {
                    background-color: #4C2F26;
                    color: white;
                    padding: 10px;
                    font-family: 'IBM Plex Sans', sans-serif;
                }
                </style>
                <h2 class='section-header'>Selecciona un dataset:</h2>
            """, unsafe_allow_html=True)

            titulos_opciones = [opcion['titulo'] for opcion in opciones]
            opcion_seleccionada = st.selectbox('', titulos_opciones, key='dataset_selectbox', label_visibility='collapsed')

            opcion_elegida = next((opcion for opcion in opciones if opcion['titulo'] == opcion_seleccionada), None)

            if opcion_elegida:
                url_datos = opcion_elegida['url']
                formato = opcion_elegida['formato']
                if url_datos:
                    datos = cargar_datos(url_datos, formato)
                    if datos is not None and not datos.empty:
                        if 'selectedLanguages' in datos.columns:
                            datos['selectedLanguages'] = datos['selectedLanguages'].astype(str)

                        # Mostrar columnas disponibles en un expander
                        with st.expander("Columnas del DataFrame"):
                            st.write(datos.columns.tolist())

                        st.markdown("""
                            <style>
                            .data-section {
                                background-color: #EAEAEA;
                                color: #00008B;
                                padding: 20px;
                                font-family: 'IBM Plex Sans', sans-serif;
                            }
                            </style>
                            <div class="data-section">
                        """, unsafe_allow_html=True)

                        st.markdown(f"<p style='color:white;'>Mostrando datos del dataset: {opcion_seleccionada}</p>", unsafe_allow_html=True)
                        st.dataframe(datos.head())

                        st.markdown("</div>", unsafe_allow_html=True)

                        # Opcional: Restablecer índice y limpiar nombres de columnas
                        if isinstance(datos.index, pd.MultiIndex):
                            datos.reset_index(inplace=True)

                        datos.columns = ['_'.join(str(s) for s in col) if isinstance(col, tuple) else str(col) for col in datos.columns]

                    else:
                        st.write("No se pudo cargar el dataset seleccionado o está vacío.")
                else:
                    st.write("No se encontró una URL de descarga para el dataset seleccionado.")
            else:
                st.write("No se encontró la opción seleccionada.")
        else:
            st.write("No hay datasets disponibles en esta página con formatos soportados.")
    else:
        st.write("No hay datasets disponibles en esta página.")

    # Estilos para los botones de paginación
    st.markdown("""
        <style>
        .pagination-button {
            background-color: #FFD100;
            color: #4C2F26;
            padding: 10px 20px;
            border: none;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
            font-family: 'IBM Plex Sans', sans-serif;
        }
        .pagination-button:hover {
            background-color: #e0b800;
        }
        </style>
    """, unsafe_allow_html=True)

    # Botones de paginación con callbacks
    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        if st.session_state.page > 0:
            st.button('Anterior', on_click=previous_page, key='previous_page_button')
    with col3:
        if datasets:
            st.button('Siguiente', on_click=next_page, key='next_page_button')
    # Mostrar número de página en blanco
    st.markdown(f"<p style='color:white; font-family: \"IBM Plex Sans\", sans-serif;'>Página {st.session_state.page + 1}</p>", unsafe_allow_html=True)

    # Añadir el pie de página al final de la página
    st.markdown("""
        <footer style="color: white; text-align: center;">
            © <a href="http://xictorlr.com" target="_blank" style="color: white;">xictorlr.com</a> | Datos extraídos de <a href="https://datos.gob.es/apidata" target="_blank" style="color: white;">datos.gob.es/apidata</a>
        </footer>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
