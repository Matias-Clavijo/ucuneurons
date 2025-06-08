import gradio as gr
import requests
import json
from typing import Dict, Any
from ..config.config import Config


class GradioInterface:
    """Vista de Gradio que se comunica con la API Flask"""

    def __init__(self, api_base_url: str = None):
        # Usar la configuración dinámica si no se proporciona una URL específica
        if api_base_url is None:
            self.api_base_url = f"http://{Config.API_HOST}:{Config.API_PORT}"
        else:
            self.api_base_url = api_base_url
        self.interface = None

    def _call_api(
        self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Método auxiliar para llamar a la API"""
        try:
            url = f"{self.api_base_url}{endpoint}"

            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            elif method == "DELETE":
                response = requests.delete(url)
            else:
                return {"status": "error", "message": f"Método {method} no soportado"}

            return response.json()

        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": f"No se puede conectar a la API Flask. Verifica que esté corriendo en {self.api_base_url}.",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def process_text_interface(self, text: str) -> str:
        """Procesar texto usando la API"""
        if not text.strip():
            return "❌ Por favor, ingresa algún texto"

        result = self._call_api("/api/process", "POST", {"text": text})

        if result.get("status") == "error":
            return f"❌ Error: {result.get('message', 'Error desconocido')}"

        data = result.get("result", {})
        return f"""✅ **Texto procesado exitosamente**

📝 **Original:** {data.get('original', '')}
🔄 **Procesado:** {data.get('processed', '')}
📏 **Longitud:** {data.get('length', 0)} caracteres
📊 **Palabras:** {data.get('word_count', 0)}
⏰ **Procesado en:** {data.get('timestamp', '')}"""

    def get_counter_status(self) -> str:
        """Obtener estado del contador"""
        result = self._call_api("/api/counter")

        if result.get("status") == "error":
            return f"❌ Error: {result.get('message', 'Error desconocido')}"

        return f"🔢 **Contador actual:** {result.get('counter', 0)}"

    def increment_counter(self) -> str:
        """Incrementar contador"""
        result = self._call_api("/api/counter", "POST")

        if result.get("status") == "error":
            return f"❌ Error: {result.get('message', 'Error desconocido')}"

        return f"✅ **Contador incrementado a:** {result.get('counter', 0)}"

    def reset_counter(self) -> str:
        """Reiniciar contador"""
        result = self._call_api("/api/counter", "DELETE")

        if result.get("status") == "error":
            return f"❌ Error: {result.get('message', 'Error desconocido')}"

        return f"🔄 **Contador reiniciado a:** {result.get('counter', 0)}"

    def get_stats(self) -> str:
        """Obtener estadísticas"""
        result = self._call_api("/api/stats")

        if result.get("status") == "error":
            return f"❌ Error: {result.get('message', 'Error desconocido')}"

        stats = result.get("stats", {})
        return f"""📊 **Estadísticas de la Aplicación**

📝 **Total de mensajes:** {stats.get('total_messages', 0)}
🔢 **Contador actual:** {stats.get('current_counter', 0)}
📋 **Entradas en historial:** {stats.get('history_entries', 0)}
⏰ **Última actualización:** {stats.get('last_updated', 'N/A')}"""

    def get_history(self) -> str:
        """Obtener historial"""
        result = self._call_api("/api/history")

        if result.get("status") == "error":
            return f"❌ Error: {result.get('message', 'Error desconocido')}"

        history = result.get("history", [])
        if not history:
            return "📋 **Historial vacío**"

        output = f"📋 **Historial de Operaciones** ({len(history)} entradas)\n\n"

        # Mostrar las últimas 10 entradas
        for entry in history[-10:]:
            action = entry.get("action", "unknown")
            timestamp = entry.get("timestamp", "N/A")
            output += f"• **{action}** - {timestamp}\n"

        if len(history) > 10:
            output += f"\n... y {len(history) - 10} entradas más"

        return output

    def clear_history(self) -> str:
        """Limpiar historial"""
        result = self._call_api("/api/history", "DELETE")

        if result.get("status") == "error":
            return f"❌ Error: {result.get('message', 'Error desconocido')}"

        return "✅ **Historial limpiado exitosamente**"

    def add_message(self, message: str) -> str:
        """Agregar mensaje"""
        if not message.strip():
            return "❌ Por favor, ingresa un mensaje"

        result = self._call_api("/api/data", "POST", {"message": message})

        if result.get("status") == "error":
            return f"❌ Error: {result.get('message', 'Error desconocido')}"

        return f"✅ **Mensaje agregado:** {message}"

    def create_interface(self) -> gr.Blocks:
        """Crear la interfaz de Gradio"""

        with gr.Blocks(
            title="Web App MVC - Gradio Interface",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                max-width: 1200px !important;
            }
            """,
        ) as interface:

            gr.Markdown("# 🚀 Web App MVC - Interfaz Gradio")
            gr.Markdown(
                "Interfaz de usuario que se comunica con la API Flask usando arquitectura MVC"
            )

            # Tab 1: Procesador de Texto
            with gr.Tab("📝 Procesador de Texto"):
                gr.Markdown("### Procesar texto usando la API Flask")

                with gr.Row():
                    with gr.Column():
                        text_input = gr.Textbox(
                            label="Texto a procesar",
                            placeholder="Escribe aquí tu texto...",
                            lines=4,
                        )
                        process_btn = gr.Button("🔄 Procesar Texto", variant="primary")

                    with gr.Column():
                        process_output = gr.Markdown(
                            label="Resultado",
                            value="Ingresa texto y presiona 'Procesar Texto'",
                        )

                process_btn.click(
                    fn=self.process_text_interface,
                    inputs=text_input,
                    outputs=process_output,
                )

            # Tab 2: Contador
            with gr.Tab("🔢 Contador"):
                gr.Markdown("### Gestión del contador")

                with gr.Row():
                    status_btn = gr.Button("📊 Ver Estado", variant="secondary")
                    increment_btn = gr.Button("➕ Incrementar", variant="primary")
                    reset_btn = gr.Button("🔄 Reiniciar", variant="stop")

                counter_output = gr.Markdown(
                    value="Presiona 'Ver Estado' para ver el contador actual"
                )

                status_btn.click(fn=self.get_counter_status, outputs=counter_output)
                increment_btn.click(fn=self.increment_counter, outputs=counter_output)
                reset_btn.click(fn=self.reset_counter, outputs=counter_output)

            # Tab 3: Datos y Mensajes
            with gr.Tab("💾 Datos"):
                gr.Markdown("### Gestión de mensajes")

                with gr.Row():
                    with gr.Column():
                        message_input = gr.Textbox(
                            label="Nuevo mensaje",
                            placeholder="Escribe un mensaje...",
                            lines=2,
                        )
                        add_message_btn = gr.Button(
                            "➕ Agregar Mensaje", variant="primary"
                        )

                    with gr.Column():
                        message_output = gr.Markdown(
                            value="Agrega un mensaje para comenzar"
                        )

                add_message_btn.click(
                    fn=self.add_message, inputs=message_input, outputs=message_output
                )

            # Tab 4: Estadísticas
            with gr.Tab("📊 Estadísticas"):
                gr.Markdown("### Estadísticas de la aplicación")

                stats_btn = gr.Button("📈 Obtener Estadísticas", variant="secondary")
                stats_output = gr.Markdown(
                    value="Presiona 'Obtener Estadísticas' para ver los datos"
                )

                stats_btn.click(fn=self.get_stats, outputs=stats_output)

            # Tab 5: Historial
            with gr.Tab("📋 Historial"):
                gr.Markdown("### Historial de operaciones")

                with gr.Row():
                    history_btn = gr.Button("📜 Ver Historial", variant="secondary")
                    clear_btn = gr.Button("🗑️ Limpiar Historial", variant="stop")

                history_output = gr.Markdown(
                    value="Presiona 'Ver Historial' para mostrar las operaciones"
                )

                history_btn.click(fn=self.get_history, outputs=history_output)
                clear_btn.click(fn=self.clear_history, outputs=history_output)

            # Footer
            gr.Markdown("---")
            gr.Markdown(
                f"""
            💡 **Información:**
            - 🌐 API Flask: http://{Config.API_HOST}:{Config.API_PORT}
            - 🎨 Interfaz Gradio: http://{Config.GRADIO_HOST}:{Config.GRADIO_PORT}
            - 🏗️ Arquitectura: Model-View-Controller (MVC)
            """
            )

        self.interface = interface
        return interface

    def launch(self, **kwargs):
        """Lanzar la interfaz"""
        if not self.interface:
            self.create_interface()

        return self.interface.launch(**kwargs)
