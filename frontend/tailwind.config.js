/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        
        // Fondo ultra oscuro
        'cyber-black': '#050505', 
        'cyber-dark': '#0a0a0a',
        'cyber-gray': '#18181b',
        
        // Manzanas Verdes (Salud / Éxito / Primary)
        'apple-green': '#39ff14', 
        'apple-green-dim': '#2abf0f',
        
        // Manzanas Rojas (Daño / Alerta / Danger)
        'apple-red': '#ff073a',
        'apple-red-dim': '#bf052b',
      },
      boxShadow: {
        'neon-green': '0 0 10px rgba(57, 255, 20, 0.5), 0 0 20px rgba(57, 255, 20, 0.3)',
        'neon-red': '0 0 10px rgba(255, 7, 58, 0.5), 0 0 20px rgba(255, 7, 58, 0.3)',
      },
      fontFamily: {
        // Si quieres una fuente más tecno, luego podemos importar una de Google Fonts
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', "Liberation Mono", "Courier New", 'monospace'],
      }
      
    },
  },

  plugins: [],
  
}
