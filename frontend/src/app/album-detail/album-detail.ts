import { Component, HostListener, OnInit, computed, inject, signal } from '@angular/core';
import { HttpClient, HttpEventType } from '@angular/common/http';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { catchError, of } from 'rxjs';

import { Album, API_URL, Media, MediaListResponse } from '../api';

@Component({
  selector: 'app-album-detail',
  imports: [RouterLink],
  templateUrl: './album-detail.html',
  styleUrl: './album-detail.css',
})
export class AlbumDetail implements OnInit {
  private http = inject(HttpClient);
  private route = inject(ActivatedRoute);

  album = signal<Album | null>(null);
  media = signal<Media[]>([]);
  total = signal(0);
  page = signal(1);
  readonly pageSize = 20;
  hasMore = computed(() => this.media().length < this.total());
  uploading = signal(false);
  error = signal('');
  uploadProgress = signal(0);
  selected = signal<Media | null>(null);

  familyId = 0;
  albumId = 0;

  ngOnInit(): void {
    this.familyId = Number(this.route.snapshot.paramMap.get('familyId'));
    this.albumId = Number(this.route.snapshot.paramMap.get('albumId'));
    this.http
      .get<Album>(`${API_URL}/families/${this.familyId}/albums/${this.albumId}`)
      .subscribe((a) => this.album.set(a));
    this.loadMedia();
  }

  loadMedia(): void {
    this.http
      .get<MediaListResponse>(
        `${API_URL}/families/${this.familyId}/albums/${this.albumId}/media`,
        { params: { page: 1, page_size: this.pageSize } }
      )
      .pipe(catchError(() => of(null)))
      .subscribe((res) => {
        if (res) {
          this.media.set(res.items);
          this.total.set(res.total);
          this.page.set(1);
        }
      });
  }

  loadMore(): void {
    const nextPage = this.page() + 1;
    this.http
      .get<MediaListResponse>(
        `${API_URL}/families/${this.familyId}/albums/${this.albumId}/media`,
        { params: { page: nextPage, page_size: this.pageSize } }
      )
      .pipe(catchError(() => of(null)))
      .subscribe((res) => {
        if (res) {
          this.media.update((items) => [...items, ...res.items]);
          this.page.set(nextPage);
        }
      });
  }

  onFilesSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const files = input.files ? Array.from(input.files) : [];
    input.value = '';
    for (const file of files) {
      this.upload(file);
    }
  }

  private upload(file: File): void {
    const form = new FormData();
    form.append('file', file);
    this.uploading.set(true);
    this.uploadProgress.set(0);
    this.http
      .post<Media>(
        `${API_URL}/families/${this.familyId}/albums/${this.albumId}/media`,
        form,
        { reportProgress: true, observe: 'events' }
      )
      .subscribe({
        next: (event) => {
          if (event.type === HttpEventType.UploadProgress && event.total) {
            this.uploadProgress.set(Math.round((event.loaded / event.total) * 100));
          } else if (event.type === HttpEventType.Response) {
            this.uploading.set(false);
            const uploaded = event.body;
            if (uploaded) {
              this.media.update((items) => [uploaded, ...items]);
              this.total.update((t) => t + 1);
            }
          }
        },
        error: (err) => {
          this.uploading.set(false);
          this.error.set(err.error?.detail ?? `Failed to upload ${file.name}`);
        },
      });
  }

  deleteMedia(item: Media): void {
    this.http
      .delete(
        `${API_URL}/families/${this.familyId}/albums/${this.albumId}/media/${item.id}`
      )
      .subscribe({ next: () => this.loadMedia() });
  }

  open(item: Media): void {
    this.selected.set(item);
  }

  close(): void {
    this.selected.set(null);
  }

  step(direction: 1 | -1): void {
    const items = this.media();
    const current = this.selected();
    if (!current) return;
    const index = items.findIndex((m) => m.id === current.id);
    const next = items[index + direction];
    if (next) this.selected.set(next);
  }

  @HostListener('document:keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    if (!this.selected()) return;
    if (event.key === 'Escape') this.close();
    if (event.key === 'ArrowRight') this.step(1);
    if (event.key === 'ArrowLeft') this.step(-1);
  }
}
