def filtrar_datasets(datasets, termino_busqueda):
    opciones = []
    for dataset in datasets:
        titulo = dataset.get('title', {}).get('es', '').lower()
        descripcion_list = dataset.get('description', [])
        descripcion = ''
        if descripcion_list:
            descripcion = descripcion_list[0].get('_value', '').lower()
        if termino_busqueda.lower() in titulo or termino_busqueda.lower() in descripcion:
            distribuciones = dataset.get('distribution', [])
            for distribucion in distribuciones:
                url_descarga = distribucion.get('accessURL', '')
                formato = distribucion.get('format', {}).get('value', '').lower()
                if formato in ['csv', 'json']:
                    opciones.append({'titulo': titulo, 'url': url_descarga, 'formato': formato})
                    break
    return opciones
