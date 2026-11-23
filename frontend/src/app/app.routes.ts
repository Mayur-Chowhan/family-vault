import { Routes } from '@angular/router';

import { AlbumDetail } from './album-detail/album-detail';
import { authGuard } from './auth/auth.guard';
import { FamilyDetail } from './family-detail/family-detail';
import { Home } from './home/home';
import { Login } from './login/login';
import { Register } from './register/register';

export const routes: Routes = [
  { path: 'login', component: Login },
  { path: 'register', component: Register },
  { path: '', component: Home, canActivate: [authGuard] },
  { path: 'families/:familyId', component: FamilyDetail, canActivate: [authGuard] },
  {
    path: 'families/:familyId/albums/:albumId',
    component: AlbumDetail,
    canActivate: [authGuard],
  },
  { path: '**', redirectTo: '' },
];
