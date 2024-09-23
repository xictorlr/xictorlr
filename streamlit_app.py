import streamlit as st
import pandas as pd
import requests
import io
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        st.write(f"Content-Type: {content_type}")
        st.write(f"URL de descarga: {url}")
        
        if 'text/html' in content_type:
            st.write("La URL devuelve contenido HTML, no un archivo de datos.")
            st.write(response.text)
            return None
        
        if 'csv' in formato or 'csv' in content_type:
            data = response.content.decode('utf-8', errors='replace')
            st.write("Contenido del dataset (primeros 500 caracteres):")
            st.code(data[:500])
            return pd.read_csv(io.StringIO(data), sep=None, engine='python')
        elif 'json' in formato or 'json' in content_type:
            data = response.json()
            if isinstance(data, dict):
                df = pd.json_normalize(data)
                return df
            elif isinstance(data, list):
                return pd.DataFrame(data)
            else:
                st.write("Formato JSON no reconocido.")
                return None
        elif 'xml' in formato or 'xml' in content_type:
            try:
                data = response.content.decode('utf-8', errors='replace')
                st.write("Contenido del dataset (primeros 500 caracteres):")
                st.code(data[:500])
                # Especifica el parser 'lxml' o 'etree'
                return pd.read_xml(io.StringIO(data), parser='lxml')
            except Exception as e:
                st.write(f"Error al cargar XML: {e}")
                return None
        elif 'excel' in formato or 'spreadsheetml' in formato:
            return pd.read_excel(io.BytesIO(response.content))
        else:
            st.write(f"Formato {formato} no soportado o contenido no válido.")
            data = response.content.decode('utf-8', errors='replace')
            st.write("Contenido del dataset (primeros 500 caracteres):")
            st.code(data[:500])
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
    st.title('Visualizador de Datasets de Datos.gob.es')

    st.warning("La verificación SSL está deshabilitada. Esto puede exponer la aplicación a riesgos de seguridad.")

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
            titulos_opciones = [opcion['titulo'] for opcion in opciones]
            opcion_seleccionada = st.selectbox('Selecciona un dataset:', titulos_opciones)

            opcion_elegida = next((opcion for opcion in opciones if opcion['titulo'] == opcion_seleccionada), None)

            if opcion_elegida:
                url_datos = opcion_elegida['url']
                formato = opcion_elegida['formato']
                if url_datos:
                    datos = cargar_datos(url_datos, formato)
                    if datos is not None and not datos.empty:
                        if 'selectedLanguages' in datos.columns:
                            datos['selectedLanguages'] = datos['selectedLanguages'].astype(str)

                        st.write(f"Mostrando datos del dataset: {opcion_seleccionada}")
                        st.dataframe(datos.head())

                        columnas = datos.columns.tolist()
                        if len(columnas) >= 2:
                            x_col = st.selectbox('Selecciona la columna para el eje X:', columnas)
                            y_col = st.selectbox('Selecciona la columna para el eje Y:', columnas)

                            if pd.api.types.is_numeric_dtype(datos[y_col]):
                                st.write(f"Gráfico de {y_col} vs {x_col}")
                                st.line_chart(datos.set_index(x_col)[y_col])
                            else:
                                st.write("La columna seleccionada para el eje Y no es numérica.")
                        else:
                            st.write("El dataset no tiene suficientes columnas para generar un gráfico.")
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

    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        if st.session_state.page > 0:
            if st.button('Anterior'):
                st.session_state.page -= 1
                st.rerun()
    with col3:
        if datasets:
            if st.button('Siguiente'):
                st.session_state.page += 1
                st.rerun()
    st.write(f"Página {st.session_state.page + 1}")

if __name__ == "__main__":
    main()
