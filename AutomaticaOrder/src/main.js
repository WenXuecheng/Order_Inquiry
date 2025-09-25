import { createApp } from 'vue';
import App from './App.vue';
import './styles.css';
import { initRouter } from './router/useSimpleRouter';

initRouter();

createApp(App).mount('#app');
