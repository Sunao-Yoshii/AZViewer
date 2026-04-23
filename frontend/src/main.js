import { createApp } from 'vue'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import './styles/app.css'
import App from './App.vue'

function preventFileDropDefaults(event) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'copy'
  }
}

window.addEventListener('dragenter', preventFileDropDefaults)
window.addEventListener('dragover', preventFileDropDefaults)
window.addEventListener('drop', preventFileDropDefaults)

createApp(App).mount('#app')
