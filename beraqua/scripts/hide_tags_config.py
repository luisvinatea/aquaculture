from traitlets.config import Config

c = Config()

# Preprocesador para eliminar completamente las celdas con "hide_export"
c.TemplateExporter.preprocessors = [
    'nbconvert.preprocessors.TagRemovePreprocessor'
]

# Configuración para ocultar celdas con etiquetas específicas
c.TagRemovePreprocessor.remove_cell_tags = {"hide_export"}

# Configuración para ocultar el input de las celdas con "hide_input"
c.TagRemovePreprocessor.remove_input_tags = {"hide_input"}
