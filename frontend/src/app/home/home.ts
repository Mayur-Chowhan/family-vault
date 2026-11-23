import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { catchError, of } from 'rxjs';

import { API_URL, Family } from '../api';
import { AuthService } from '../auth/auth.service';

@Component({
  selector: 'app-home',
  imports: [FormsModule, RouterLink],
  templateUrl: './home.html',
  styleUrl: './home.css',
})
export class Home implements OnInit {
  private http = inject(HttpClient);
  protected auth = inject(AuthService);

  families = signal<Family[]>([]);
  newFamilyName = '';
  error = signal('');

  ngOnInit(): void {
    this.loadFamilies();
  }

  loadFamilies(): void {
    this.http
      .get<Family[]>(`${API_URL}/families`)
      .pipe(
        catchError(() => {
          this.auth.logout();
          return of([]);
        })
      )
      .subscribe((families) => this.families.set(families));
  }

  createFamily(): void {
    const name = this.newFamilyName.trim();
    if (!name) return;
    this.http.post<Family>(`${API_URL}/families`, { name }).subscribe({
      next: () => {
        this.newFamilyName = '';
        this.loadFamilies();
      },
      error: (err) =>
        this.error.set(err.error?.detail ?? 'Failed to create family'),
    });
  }
}
