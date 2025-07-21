import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../views/HomePage.vue'
import TranscribeTest from '../views/TranscribeTest.vue'
import LLMTest from '../views/LLMTest.vue'
import TTSTest from '../views/TTSTest.vue'
import RealtimeChat from '../views/RealtimeChat.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomePage
  },
  {
    path: '/transcribe',
    name: 'TranscribeTest',
    component: TranscribeTest
  },
  {
    path: '/llm',
    name: 'LLMTest',
    component: LLMTest
  },
  {
    path: '/tts',
    name: 'TTSTest',
    component: TTSTest
  },
  {
    path: '/realtime',
    name: 'RealtimeChat',
    component: RealtimeChat
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 