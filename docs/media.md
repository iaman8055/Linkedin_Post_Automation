# Media attachments

Phase 19 adds user-uploaded media to draft posts without storing large binary values in PostgreSQL.
The post model already supported image, video, and document metadata, so no schema migration was needed.

## Supported uploads

- JPEG, PNG, GIF, and WebP images, up to 10 MiB by default;
- MP4 video, up to 50 MiB by default;
- PDF documents, up to 10 MiB by default;
- up to ten attachments per post.

The backend checks both the declared MIME type and the file signature. Original names are sanitized and
stored as display metadata; generated opaque keys determine the storage location. Uploads are read with a
hard upper bound before being passed to storage.

Media can be added to or removed from drafts only. Retrieval, listing, upload, and deletion all verify the
authenticated owner. Deleting an attachment removes both its metadata and stored binary. If database
creation fails after a binary is written, the service removes the orphaned file.

## Storage architecture

`MediaStorage` isolates binary persistence behind `put`, `read`, and `delete` operations. The included
`LocalMediaStorage` is for development and tests. It resolves every key under one configured root and
rejects path traversal.

```env
STORAGE_PROVIDER=local
STORAGE_LOCAL_PATH=./storage
STORAGE_MAX_IMAGE_BYTES=10485760
STORAGE_MAX_VIDEO_BYTES=52428800
STORAGE_MAX_DOCUMENT_BYTES=10485760
```

Docker Compose mounts `media_data` at `/app/storage`, so development uploads survive backend container
restarts. Local storage is rejected when `APP_ENV=production`. A real S3-compatible adapter is included
for AWS S3, MinIO, and compatible managed services:

```env
STORAGE_PROVIDER=s3
STORAGE_BUCKET=linkedin-media
STORAGE_REGION=ap-south-1
STORAGE_ENDPOINT=
STORAGE_ACCESS_KEY=
STORAGE_SECRET_KEY=
```

The endpoint and explicit credentials are optional for standard AWS deployments using the SDK's IAM
role or workload-identity credential chain. Without a usable local or S3 configuration, the API returns
`MEDIA_STORAGE_NOT_CONFIGURED` instead of pretending an upload succeeded.

For Supabase Storage, enable its S3 protocol, create a private bucket, and generate server-side S3
access credentials in the Supabase dashboard:

```env
STORAGE_PROVIDER=supabase_s3
STORAGE_BUCKET=linkedin-media
STORAGE_REGION=your-project-region
STORAGE_ENDPOINT=https://PROJECT_REF.storage.supabase.co/storage/v1/s3
STORAGE_ACCESS_KEY=your-s3-access-key
STORAGE_SECRET_KEY=your-s3-secret-key
STORAGE_FORCE_PATH_STYLE=true
```

The Supabase adapter forces AWS Signature V4 and path-style addressing. These credentials bypass Row
Level Security and must stay on the backend; never expose them through Vite variables or browser code.
Application ownership checks still protect every media route.

## API

- `POST /api/v1/posts/{post_id}/media?filename=...` accepts the raw file body and its `Content-Type`.
- `GET /api/v1/posts/{post_id}/media` lists owned attachment metadata.
- `GET /api/v1/media/{media_id}/content` retrieves owned binary content.
- `DELETE /api/v1/media/{media_id}` removes an attachment from a draft.

## LinkedIn limitation

Attachment storage does not enable LinkedIn media publishing. The current publisher still calls the
verified text-only Posts API flow. LinkedIn image, video, and document publishing require separate upload
registration, asset handling, permissions, and idempotency work. The application therefore labels stored
attachments as text-publishing unavailable rather than silently dropping or faking them.
