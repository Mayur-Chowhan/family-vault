import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { catchError, of } from 'rxjs';

import { Album, API_URL, Family } from '../api';

@Component({
  selector: 'app-family-detail',
  imports: [FormsModule, RouterLink],
  templateUrl: './family-detail.html',
  styleUrl: './family-detail.css',
})
export class FamilyDetail implements OnInit {
  private http = inject(HttpClient);
  private route = inject(ActivatedRoute);

  family = signal<Family | null>(null);
  albums = signal<Album[]>([]);
  newAlbumName = '';
  error = signal('');

  familyId = 0;

  ngOnInit(): void {
    this.familyId = Number(this.route.snapshot.paramMap.get('familyId'));
    this.http
      .get<Family>(`${API_URL}/families/${this.familyId}`)
      .subscribe((f) => this.family.set(f));
    this.loadAlbums();
  }

  loadAlbums(): void {
    this.http
      .get<Album[]>(`${API_URL}/families/${this.familyId}/albums`)
      .pipe(catchError(() => of([])))
      .subscribe((albums) => this.albums.set(albums));
  }

  createAlbum(): void {
    const name = this.newAlbumName.trim();
    if (!name) return;
    this.http
      .post<Album>(`${API_URL}/families/${this.familyId}/albums`, { name })
      .subscribe({
        next: () => {
          this.newAlbumName = '';
          this.loadAlbums();
        },
        error: (err) => this.error.set(err.error?.detail ?? 'Failed to create album'),
      });
  }
}
