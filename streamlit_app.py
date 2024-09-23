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
        st.markdown(f"**<span style='color:white;'>URL de descarga:</span>** {url}", unsafe_allow_html=True)
        
        if 'text/html' in content_type:
            st.write("La URL devuelve contenido HTML, no un archivo de datos.")
            st.write(response.text)
            return None
        
        if 'csv' in formato or 'csv' in content_type:
            data = response.content.decode('utf-8', errors='replace')
            df = pd.read_csv(io.StringIO(data), sep=None, engine='python')
            return df
        elif 'json' in formato or 'json' in content_type:
            data = response.json()
            if isinstance(data, dict):
                df = pd.json_normalize(data)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                st.write("Formato JSON no reconocido.")
                return None
            return df
        elif 'xml' in formato or 'xml' in content_type:
            try:
                data = response.content.decode('utf-8', errors='replace')
                df = pd.read_xml(io.StringIO(data))
                return df
            except Exception as e:
                st.write(f"Error al cargar XML: {e}")
                return None
        elif 'excel' in formato or 'spreadsheetml' in formato:
            df = pd.read_excel(io.BytesIO(response.content))
            return df
        else:
            st.write(f"Formato {formato} no soportado o contenido no válido.")
            data = response.content.decode('utf-8', errors='replace')
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
        /* Cambiar el color del texto y fondo del título del expander */
        .streamlit-expanderHeader {
            color: white;
        }
        /* Cambiar el color de fondo de toda la aplicación */
        .stApp {
            background-color: #4C2F26;
            padding-bottom: 70px;
        }
        /* Cambiar el color del texto para garantizar legibilidad */
        html, body, [class*="css"]  {
            color: white;
        }
        /* Estilos para inputs y selects */
        input, select, textarea {
            background-color: #FFFFFF !important;
            color: #4C2F26 !important;
        }
        /* Estilos para las etiquetas */
        label {
            color: white;
        }
        /* Estilos para los botones */
        .stButton>button {
            background-color: #FFD100;
            color: #4C2F26;
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
        }
        footer a {
            color: white !important;
            text-decoration: none;
        }
        /* Asegurar que el título se muestre en blanco */
        .hero h1 {
            color: white !important;
        }
        /* Cambiar el color del texto del título del expander */
        .streamlit-expanderHeader {
            color: white !important;
        }
        /* Cambiar el color del texto y fondo del título del expander */
        .streamlit-expanderHeader {
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Encabezado de la aplicación
    st.markdown("""
        <div class="hero">
            <h1>Visualizador de Datasets de Datos.gob.es</h1>
        </div>
    """, unsafe_allow_html=True)

    #st.warning("La verificación SSL está deshabilitada. Esto puede exponer la aplicación a riesgos de seguridad.")

    if 'page' not in st.session_state:
        st.session_state.page = 0

    datasets, total_items = obtener_datasets_pagina(st.session_state.page)

    if datasets:
        opciones = []
        for dataset in datasets:
            titulo = obtener_titulo(dataset)
            distribuciones = dataset.get('distribution', [])
            for distribucion in distribuciones:
                url_descarga = distribucion.get('accessURL', '')
                formato = distribucion.get('format', {}).get('value', '').lower()
                opciones.append({'titulo': titulo, 'url': url_descarga, 'formato': formato})
                break
        if opciones:
            st.markdown("""
                <style>
                .section-header {
                    background-color: #4C2F26;
                    color: white;
                    padding: 10px;
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
                            st.markdown(
                    '''
                    <style>
                    .streamlit-expanderHeader {
                        background-color: white;
                        color: black; # Adjust this for expander header color
                    }
                    .streamlit-expanderContent {
                        background-color: white;
                        color: black; # Expander content color
                    }
                    </style>
                    ''',
                    unsafe_allow_html=True
                             )

                        # Mostrar columnas disponibles en un expander
                        with st.expander("Columnas del DataFrame"):
                            st.write(datos.columns.tolist())

    

                        st.markdown(f"<p style='color:white;'>Mostrando datos del dataset: {opcion_seleccionada}</p>", unsafe_allow_html=True)
                        st.dataframe(datos.head())

                        st.markdown("</div>", unsafe_allow_html=True)

                        # Opcional: Restablecer índice y limpiar nombres de columnas
                        if isinstance(datos.index, pd.MultiIndex):
                            datos.reset_index(inplace=True)

                        datos.columns = ['_'.join(str(s) for s in col) if isinstance(col, tuple) else str(col) for col in datos.columns]

                        # Eliminamos la funcionalidad de generar gráficos

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
        }
        .pagination-button:hover {
            background-color: #e0b800;
        }
        </style>
    """, unsafe_allow_html=True)

    # Botones de paginación
    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        if st.session_state.page > 0:
            if st.button('Anterior'):
                st.session_state.page -= 1
                st.experimental_rerun()
    with col3:
        if datasets:
            if st.button('Siguiente'):
                st.session_state.page += 1
                st.experimental_rerun()
    # Mostrar número de página en blanco
    st.markdown(f"<p style='color:white;'>Página {st.session_state.page + 1}</p>", unsafe_allow_html=True)

    # Añadir el pie de página al final de la página
    st.markdown("""
        <footer style="color: white; text-align: center;">
            © <a href="http://xictorlr.com" target="_blank" style="color: white;">xictorlr.com</a> | Datos extraídos de <a href="https://datos.gob.es/apidata" target="_blank" style="color: white;">datos.gob.es/apidata</a>
        </footer>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
