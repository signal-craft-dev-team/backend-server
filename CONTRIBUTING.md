# Docker Image 태그 전략

이 문서는 `backend-server` 의 Docker 이미지 태그 규칙을 정의합니다. 목표는 GitHub PR, dev merge, staging 검증, main 승격까지의 배포 흐름에서 **추적 가능성**, **재현성**, **롤백 가능성**을 유지하는 것입니다.

## 배경

이 저장소는 다음 두 기능을 하나의 VM 위에서 Docker 컨테이너로 운영합니다.

- MQTT subscriber: 디바이스 신호 수신 및 DB 저장
- Presigned URL API: 디바이스 업로드용 URL 발급

배포는 GitHub Actions에서 이미지를 빌드하고, GCP Artifact Registry로 push한 뒤, VM에서 pull 및 재시작하는 흐름을 기준으로 합니다.

이 저장소의 공통 환경변수 이름은 `.env.example` 를 기준으로 맞추며, 대표적으로 `GOOGLE_CLOUD_PROJECT`, `GCS_AUDIO_BUCKET`, `GCS_AUDIO_PREFIX`, `MQTT_*` 계열을 사용합니다.

## 핵심 원칙

1. 배포 기준은 가변 태그가 아니라 **불변 태그**를 우선한다.
2. 사람이 읽기 쉬운 태그와 기계가 추적하기 쉬운 태그를 함께 사용한다.
3. staging과 main은 가능하면 **같은 이미지 digest**를 기준으로 승격한다.
4. `latest` 는 편의용 alias 로만 사용하고, 배포 기준으로 사용하지 않는다.

## 권장 태그 구조

이미지에는 최소 2종류의 태그를 붙이는 것을 권장합니다.

### 1. 환경/브랜치 의미 태그

브랜치별로 현재 배포 대상임을 빠르게 식별하기 위한 태그입니다.

- dev 브랜치: `dev-0.0.1`
- main 브랜치: `main-0.1.0`

이 태그는 사람이 보기 쉽지만, 단독으로는 재빌드/덮어쓰기 위험이 있습니다. 따라서 단독 사용보다 아래의 불변 태그와 함께 사용해야 합니다.

### 2. 불변 추적 태그

커밋 기준으로 고정되는 태그입니다.

- 예시: `sha-abc1234`
- 또는 예시: `dev-0.0.1-abc1234`

이 태그는 같은 커밋에 대해 동일한 이미지를 다시 참조할 수 있게 해 주므로, staging 검증과 롤백에 유리합니다.

### 3. 편의용 alias 태그

최근 빌드를 빠르게 가리키는 보조 태그입니다.

- dev 브랜치: `dev-latest`
- main 브랜치: `main-latest`

alias 태그는 운영 편의용이며, 배포 대상의 정합성은 항상 불변 태그로 확인합니다.

## 추천 조합

실제로는 아래 조합을 권장합니다.

### dev 브랜치

- `dev-0.0.1`
- `dev-0.0.1-<short-sha>`
- `sha-<short-sha>`
- `dev-latest`

### main 브랜치

- `main-0.1.0`
- `main-0.1.0-<short-sha>`
- `sha-<short-sha>`
- `main-latest`

## 태그 생성 규칙

1. PR 단계에서는 이미지를 배포하지 않고, 빌드 가능성만 확인한다.
2. dev merge 시 이미지를 빌드하고 Artifact Registry에 push 한다.
3. staging VM은 `dev` 계열 태그 중 불변 태그를 pull 한다.
4. staging 검증이 끝나면 동일 digest를 `main` 계열 태그로 승격한다.
5. main VM은 `main` 계열 태그를 pull 한다.

## 배포 흐름 예시

1. `feature/*` -> PR 생성
2. PR 검증 통과
3. `dev` merge
4. CI에서 이미지 빌드
5. Artifact Registry에 push
6. staging VM이 `dev-0.0.1-abc1234` pull
7. staging 수동 검증
8. 승인 후 `main-0.1.0-abc1234` 또는 동일 digest에 `main-0.1.0` 추가
9. main VM이 pull 후 재시작

## 추천 운영 방식

### 권장

- 배포는 항상 SHA 포함 태그로 고정한다.
- 버전 숫자(`0.0.1`, `0.1.0`)는 사람을 위한 기준으로만 사용한다.
- staging 검증 후 main 승격 시 같은 이미지를 재사용한다.
- VM 재시작은 `docker compose pull` 후 `docker compose up -d` 패턴을 우선 고려한다.

### 비권장

- `latest` 만으로 배포 관리하기
- dev와 main을 서로 다른 소스에서 다시 빌드하기
- staging 검증 없이 main 승격하기
- 불변 태그 없이 가변 태그만 사용하기

## GCP Artifact Registry 접근 방식

배포 자동화가 GitHub Actions에서 실행될 경우, GCP 인증은 다음 우선순위를 권장합니다.

1. Workload Identity Federation
2. 서비스 계정 키 임시 사용

장기 운영과 보안 관점에서는 Workload Identity Federation 이 더 적합합니다.

## 결론

이 저장소의 태그 전략은 다음 한 줄로 요약할 수 있습니다.

**사람이 읽는 브랜치 버전 태그 + 커밋 기반 불변 태그 + 편의용 latest alias**

이 규칙을 기준으로 GitHub Actions, Artifact Registry, VM pull/restart workflow를 구현합니다.