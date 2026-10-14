import { createRouter, createWebHistory } from 'vue-router';
export const router = createRouter({
  history:createWebHistory(),
  routes:[
    {path:'/',component:()=>import('./views/Problems.vue')},
    {path:'/problems/:id',component:()=>import('./views/Problem.vue')},
    {path:'/submissions',component:()=>import('./views/Submissions.vue')},
    {path:'/contests',component:()=>import('./views/Contests.vue')},
    {path:'/contests/:id',component:()=>import('./views/Contest.vue')},
    {path:'/community',component:()=>import('./views/Community.vue')},
    {path:'/workspace',component:()=>import('./views/Workspace.vue')},
    {path:'/admin',component:()=>import('./views/Admin.vue')},
    {path:'/auth',component:()=>import('./views/Auth.vue')},
    {path:'/users/:id',component:()=>import('./views/Profile.vue')},
    {path:'/:pathMatch(.*)*',redirect:'/'}
  ]
});

