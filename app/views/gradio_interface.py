import gradio as gr
import requests
import json
from typing import Dict, Any
import base64
from io import BytesIO

class GradioInterface:
    """Vista de Gradio que se comunica con la API Flask"""
    
    def __init__(self, api_base_url: str = "http://localhost:5000", session_id: str = None):
        self.api_base_url = api_base_url
        self.session_id = session_id
        self.interface = None
    
    def _call_api(self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Método auxiliar para llamar a la API"""
        try:
            url = f"{self.api_base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            else:
                return {"status": "error", "message": f"Método {method} no soportado"}
            
            return response.json()
            
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": "No se puede conectar a la API Flask. Verifica que esté corriendo en el puerto 5000."
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def process_text_interface(self, chemicals, place, materials, frequency, environment, additional_info, process, image_pil) -> str:
        
        required_fields = {
            "Chemicals": chemicals,
            "Place": place,
            "Materials": materials,
            "Frequency of use": frequency,
            "Environment": environment,
            "Process": process,
        }
        empty_fields = [name for name, value in required_fields.items() if not str(value).strip()]

        if empty_fields:
            missing_fields_str = ", ".join(empty_fields)
            return f"❌ Please fill in all required fields. Missing: {missing_fields_str}."

        payload = {
            "chemicals": chemicals,
            "place": place,
            "materials": materials,
            "frequency": frequency,
            "environment": environment,
            "additional_info": additional_info,
            "process": process,
        }
 
        if image_pil:
            buffered = BytesIO()
            image_pil.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            payload['image_base64'] = img_str

        print("Sending payload to API:", payload)
        #result = self._call_api("/api/process", "POST", payload)
        result = {"status": "success", "result": {"original": "Hello", "processed": "Hello", "length": 5, "word_count": 1, "timestamp": "2025-06-07T12:00:00Z"}}
        if result.get("status") == "error":
            return f"❌ Error: {result.get('message', 'Error desconocido')}"
        
        data = result.get("result", {})
        return f"""✅ **Texto procesado exitosamente**

📝 **Original:** {data.get('original', '')}
🔄 **Procesado:** {data.get('processed', '')}
📏 **Longitud:** {data.get('length', 0)} caracteres
📊 **Palabras:** {data.get('word_count', 0)}
⏰ **Procesado en:** {data.get('timestamp', '')}"""
          
    def create_interface(self) -> gr.Blocks:
        """Crear la interfaz de Gradio"""
        
        with gr.Blocks(
            title="Ucuneurons",
            theme=gr.themes.Base()
        ) as interface:
            
            gr.Markdown("# 🚀 Ucuneurons")
            
            # Tab 1: Procesador de Texto
            with gr.Tab("📝 Environmental Health and Safety Professionals Optimizer"):
                gr.Markdown("### Complete the form")
                
                with gr.Row():
                    with gr.Column():
                        chemicals_input = gr.Textbox(
                            label="Chemicals",
                            placeholder="Write the chemicals that are involved (Ej: Pentanol)"
                        )
                        place_input = gr.Textbox(
                            label="Place",
                            placeholder="Write the place of the factory (Ej: Planta 1 Rosario, Argentina)"
                        )
                        materials_input = gr.Textbox(
                            label="Materials",
                            placeholder="Write the materials that are involved (Ej: Bomb)"
                        )
                        frequency_of_use_input = gr.Textbox(
                            label="Frequency of use",
                            placeholder="Specify the frequency in which the operator repeats the process (Ej: 10 times a day)"
                        )
                        environment_input = gr.Textbox(
                            label="Environment",
                            placeholder="Is indoor or outdoor (you can specified wheather)"
                        )
                        process_input = gr.Textbox(
                            label="Process",
                            placeholder="Write the process to do (Ej: Move 3 feets)",
                            lines=4
                        )
                        additional_info_input = gr.Textbox(
                            label="Additional information",
                            placeholder="You can specify additional information that you think is important",
                            lines=4
                        )
                        process_btn = gr.Button("🔄 Process", variant="primary")
                    
                    with gr.Column():
                        image_input = gr.Image(label="Image", type="pil")
                        process_output = gr.Markdown(
                            label="Result",
                            value="Ingresa texto y presiona 'Procesar Texto'"
                        )
                
                process_btn.click(
                    fn=self.process_text_interface,
                    inputs=[
                        chemicals_input,
                        place_input,
                        materials_input,
                        frequency_of_use_input,
                        environment_input,
                        additional_info_input,
                        process_input,
                        image_input
                    ],
                    outputs=process_output
                )
        
        self.interface = interface
        return interface
    
    def launch(self, **kwargs):
        """Lanzar la interfaz"""
        if not self.interface:
            self.create_interface()
        
        return self.interface.launch(**kwargs) 