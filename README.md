# 리버티 와일드 위키

운영 Fabric 서버의 플레이어 콘텐츠를 소개하는 가벼운 한국어 정적 위키입니다. 대상 주소는 `https://wiki.libertywild.org`입니다.

저장소: [Harusarri/liberty-wild-wiki](https://github.com/Harusarri/liberty-wild-wiki) · [자동 배포 기록](https://github.com/Harusarri/liberty-wild-wiki/actions/workflows/pages.yml)

운영 서버의 설치 모드 96개를 검토해 플레이어용 안내와 클라이언트 도움말 36개를 작성했습니다. 모든 안내를 짧은 단계와 이미지 중심으로 구성했으며, 29개 문서에는 실제 화면 사진을 넣었습니다. 사진 자산은 49장으로, 로컬 공허 촬영장의 게임 사진 44장·공개 웹 지도 화면 1장·서버 자료실의 안내 화면 4장입니다. 로컬 게임 사진은 아침 시간과 Complementary Reimagined 셰이더로 촬영했습니다. 메뉴와 문서에는 실제 Minecraft·Farmer’s Delight 아이템 이미지 24종을 사용합니다.

## 로컬 미리 보기

Python 3.13 이상만 필요합니다. npm이나 패키지 설치, 외부 API 키는 필요하지 않습니다.

```bash
python3 scripts/build.py
python3 scripts/check.py
python3 -m http.server 8766 --bind 127.0.0.1 --directory dist
```

브라우저에서 `http://127.0.0.1:8766`을 엽니다. `dist/`가 완성된 사이트입니다.

## GitHub Pages 게시

1. 이 저장소를 GitHub에 올립니다. 공개용 문서와 사이트 소스만 포함합니다.
2. 저장소 **Settings → Pages → Source**를 **GitHub Actions**로 설정합니다.
3. `main`에 푸시하거나 **Actions → Publish wiki → Run workflow**를 실행합니다.
4. Pages의 **Custom domain**에 `wiki.libertywild.org`를 저장합니다. Actions 방식은 `CNAME` 파일만으로 Custom domain 설정이 완료되지 않습니다.
5. DNS에 `wiki` CNAME 레코드를 `<GitHub 계정 또는 조직>.github.io`로 지정합니다. 저장소 이름이나 URL 경로는 넣지 않습니다. 기존 게임 접속용 A/SRV 레코드는 바꾸지 않습니다.
6. GitHub의 DNS 확인과 인증서 발급이 끝나면 **Enforce HTTPS**를 켭니다.
7. 실제 도메인에서 문서·검색·모바일 메뉴·오프라인 재열기를 확인합니다.

현재 Cloudflare DNS 연결값은 다음과 같습니다.

| 항목 | 값 |
| --- | --- |
| 도메인 | `libertywild.org` |
| 유형 | `CNAME` |
| 이름 | `wiki` |
| 대상 | `harusarri.github.io` |
| 프록시 상태 | DNS 전용 |
| TTL | 자동 |

문서를 수정한 뒤 `main`에 푸시하면 GitHub Actions가 빌드와 링크 검사를 수행하고 Pages에 배포합니다. 게임 서버나 별도의 웹 서버 프로세스를 재시작할 필요가 없습니다.

[GitHub 공식 배포 안내](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) · [사용자 지정 도메인 안내](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)

## 문서 수정

`content/*.json` 안의 문서를 수정합니다. 각 문서는 `slug`, `title`, `category`, `summary`, `order`, `mods`, `body_markdown`, `sources`를 가집니다. 제목과 본문 검색 자료는 빌드할 때 자동 생성됩니다. 문서 링크는 `/guide/문서-slug/` 형식으로 작성합니다.

- `body_markdown`: 처음 읽을 짧은 소개입니다.
- `icon_asset`: `assets/item-icons/`에 있는 실제 아이템 PNG 파일명입니다.
- `visual_steps`: `title`, `caption`으로 순서를 설명합니다. `photo`에는 `media/photos.json`의 사진 키를 넣고, 사진이 없는 단계에는 `icon_asset` 아이템 그림을 사용합니다. 단계 번호는 자동 생성합니다.
- `markers`: 단계 사진에 붙일 클릭 위치입니다. 각 항목은 사진의 원본 해상도 기준 `x`, `y`, `label`을 가집니다. 사진의 `focus` 범위를 벗어나면 빌드가 실패합니다. 로컬 게임 사진의 기본 해상도는 1600×900입니다.
- `details`: `title`, `body_markdown`으로 긴 설명을 접어 둡니다. 처음 화면에는 필요한 조작만 남깁니다.

사진은 원본을 조작하지 않고 WebP 640·1280·1600 폭으로 저장합니다. `media/photos.json`에 대체 설명·캡션·변형 파일을 등록하고, 필요하면 `focus: [x, y, width, height]`로 GUI를 강조합니다. 클릭 표시와 화면 강조는 HTML/CSS이며, 사진을 누르면 원본 구도로 크게 열립니다. `media/PROVENANCE.json`에 촬영 조건과 원본 해시를 기록합니다. 웹 지도에는 게임 촬영 조건을 붙이지 않습니다. 자료실 사진에는 `kind: "community"`, 원본 `width`·`height`, 영구 메시지 링크 `source_url`을 넣습니다. Discord CDN의 만료되는 첨부 주소는 공개 저장소에 넣지 않습니다. `details`에는 선택적으로 `diagram` SVG 파일명을 지정해 배치도를 함께 표시할 수 있습니다.

실제 설치 버전과 설정을 함께 확인하고, 일반 플레이어에게 허용된 기능만 설명합니다. 메뉴·버튼·우클릭 경로를 우선하며, GUI를 여는 다른 방법이 없는 경우에만 허용된 최소 명령을 안내합니다. 권한 노드가 없다는 이유만으로 허용 여부를 단정하지 않고 실제 코드의 기본 권한도 확인합니다. 설정 원본, DB 접속 정보, 플레이어 데이터, 모드 JAR와 내부 감사 자료는 이 저장소에 추가하지 않습니다. 제작자 문서 링크는 각 페이지의 `sources`에 넣습니다.

## 속도와 캐싱

본문은 모두 HTML로 생성됩니다. 외부 폰트·분석 스크립트·JavaScript 프레임워크는 사용하지 않습니다. 검색 인덱스는 검색을 열 때 가져오며, Service Worker 설치 시 오프라인 검색용으로도 저장합니다.

CSS·JavaScript·아이콘·검색 파일은 내용 해시를 파일명에 포함합니다. 같은 버전의 자산은 캐시에서 읽고, 방문한 문서는 저장본을 먼저 보여 준 뒤 온라인일 때 갱신합니다. 캐시는 최대 80개의 방문 문서를 유지하며 빌드 버전이 바뀌면 오래된 캐시를 정리합니다. 첫 방문과 캐시가 없는 문서는 인터넷 연결이 필요합니다. GitHub Pages의 HTTP 응답 헤더를 임의로 설정하는 방식은 사용하지 않습니다.

아이템 PNG 24종은 합계 약 5.5KB이며 초기 캐시에 포함합니다. 사진은 화면 가까이 스크롤했을 때 불러오고, 읽은 사진만 저장합니다. Service Worker는 HTTPS 또는 localhost에서 동작합니다. 초기 캐시 목록의 중복 URL은 빌드 시 제거하여 설치 실패를 방지합니다.

기본 경로는 상대 주소로 처리하므로 GitHub 프로젝트 주소에서도 본문과 자산을 미리 볼 수 있습니다. 오류 페이지의 복구 링크와 검색 엔진 canonical 주소는 최종 사용자 지정 도메인을 기준으로 합니다.

## 자산 출처

- Obsidianotion의 밝은 색상·글꼴 구성을 웹에 맞게 수정했습니다. Unlicense. `vendor/obsidianotion/`에 원본·라이선스·고정 커밋·해시를 보관합니다.
- Lucide 아이콘은 ISC License입니다. `vendor/lucide/`에 사용한 SVG와 라이선스를 보관합니다.
- 메뉴·문서·단계의 아이템 PNG는 Minecraft 26.3과 Farmer’s Delight Refabricated의 원본 텍스처입니다. `assets/item-icons/manifest.json`에 각 파일의 출처·해시·권리자를 기록하며, Farmer’s Delight의 MIT 고지를 함께 보관합니다. Minecraft의 권리는 Mojang AB / Microsoft에 있습니다.
- python-markdown2 2.5.3은 MIT License입니다. `vendor/markdown2/`에 빌드용 소스와 라이선스를 보관합니다.

게임 사진은 별도의 로컬 공허 촬영장에서 아침 시간과 Complementary Reimagined 셰이더로 촬영합니다. 게임 화면은 운영 설정을 반영한 일반 사용자 계정으로 확인하며, 운영 서버의 건물·플레이어·채팅을 촬영한 자료와 혼동하지 않도록 캡션에 촬영 조건을 적습니다. 공개 웹 지도 화면은 별도로 표시합니다. 모든 사진을 모든 문서에 쓰는 것은 아니며, 모든 기능을 운영 서버에서 직접 시험했다는 의미도 아닙니다. 모드·셰이더·Minecraft의 권리는 각 제작자에게 있습니다.

## 자료실 반영 기준

2026년 10월 10일 Discord 자료실 `1475435085045170317`의 글 15개와 메시지 158개를 검토했습니다. 채택한 글은 각 문서의 참고 자료와 사진 캡션에 원문 링크를 남깁니다. 원문을 보려면 Discord 로그인과 해당 채널 접근 권한이 필요합니다. 대화 전체, 계정 식별 정보, 인증 자료는 저장소에 싣지 않습니다.

현재 구현과 다른 예전 안내는 그대로 복사하지 않습니다. 이번에는 머리 제작 결과를 1개로, 웹 지도 선택을 왼쪽 드래그로 바로잡았고, 스컬크 장거리 안테나는 감지체 사이 Y 차이 17블록 이상으로 명시했습니다. 라이트메티카·Prism 사진은 자료실의 당시 화면이며 새 촬영장 사진과 구분합니다. 관리자용 Axiom 스크립트, 버전 검증이 안 된 기반암 영상, 개인 워프 좌표 자료는 일반 플레이어 사용법에 합치지 않았습니다.
