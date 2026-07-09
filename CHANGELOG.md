# 변경 이력 (CHANGELOG)

나라장터 발주정보 확인 대시보드의 주요 변경 기록.
(운영 상세·계정 정보는 로컬 전용 `HANDOFF.md` 참고 — 이 파일에는 비밀정보를 넣지 않음)

## 2026-07-09 — 전면 개편

Railway(유료) 서비스 만료로 대시보드가 다운된 것을 계기로 무료·안전 구조로 재구축.

### 아키텍처
- **호스팅**: Railway/FastAPI(유료) → **GitHub Pages 정적**(무료)로 전환.
  - data.go.kr 공공데이터 API가 HTTPS + CORS를 지원해 별도 백엔드 서버 없이 운영 가능.
  - 기존 FastAPI 백엔드는 `legacy_railway_backend/`로 이관(미사용, 참고용).
- **데이터 조회**: Cloudflare Worker 프록시 경유.
  - 브라우저는 프록시만 호출하고, 프록시가 전체 페이지네이션을 수행해 합쳐서 반환.
  - **API 키는 Worker Secret에만 보관** → 클라이언트/저장소에 노출되지 않음.
- **도메인**: `https://bid.maestro4u.kr` 커스텀 서브도메인 연결, HTTPS 강제.
- **배포**: `git push origin main` → GitHub Actions(`.github/workflows/pages.yml`)가 `static/` 자동 배포.

### 기능
- **제목 변경**: "나라장터 입찰 대시보드" → "나라장터 발주정보 확인 대시보드".
- **최소 예산 표기**: 천단위 콤마 + "원" 단위 표시(실시간 포맷).
- **내 보관함**: 검색결과에서 ☆로 담기 → 개인별 localStorage 저장.
  - 스냅샷 저장(마감·검색창에서 사라져도 유지), 재부팅해도 유지, 계속 누적.
  - 항목별 메모, 보관 해제, JSON 백업(내보내기)/복원(불러오기).
- **엑셀 내보내기**: 보관함을 `PreResult`(사전규격)/`BidResult`(입찰공고) 2시트 xlsx로 저장.
  - 사내 검토 양식과 동일한 컬럼 구성. 라이브러리(SheetJS)는 `static/vendor/`에 동봉.

### 보안
- 클라이언트/저장소/git 히스토리에서 API 키 제거(git-filter-repo로 히스토리 재작성).
- data.go.kr 키 재발급 시 Worker Secret 교체만으로 반영(대시보드 수정 불필요).

## 이전 (Railway 시절, ~2026-04)
- FastAPI + 정적 HTML을 Railway에 배포, 브라우저 필터 조회.
- n8n 워크플로로 매일 텔레그램 알림(현재도 별도 동작 중).
