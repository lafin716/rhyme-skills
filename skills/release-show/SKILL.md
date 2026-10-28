---
name: release-show
description: make-release 스킬로 릴리즈(커밋·검증·버전 업·태그·릴리즈 노트 공개)를 끝낸 뒤 이어서 show-dev 스킬로 개발 서버를 LAN·Tailscale 주소로 연다. "/release-show", "릴리즈하고 개발 서버 띄워줘", "배포하고 폰에서 볼 링크" 같은 요청에 사용.
argument-hint: "[버전|patch|minor|major] [-- show-dev 인자]"
---

# release-show — 릴리즈 후 개발 서버 열기

인자: `$ARGUMENTS`
- `--` 앞은 make-release 인자(버전·`patch`/`minor`/`major`, 비면 make-release가 판단), 뒤는 show-dev 인자(앱 경로·스크립트·포트, 비면 show-dev가 판단).
- `--`가 없으면 버전 꼴(`v1.2.3`, `1.2.3`, `patch`/`minor`/`major`, 프리릴리즈 꼴)인 토큰만 make-release로, 나머지는 show-dev로 보낸다.

이 스킬을 호출한 것은 make-release가 요구하는 **이번 릴리즈 승인**과 show-dev 실행 요청을 함께 준 것이다. 승인 범위와 금지 사항은 각 스킬 문서를 그대로 따른다.

## 1. make-release 실행
- 같은 저장소의 `make-release` 스킬을 불러 끝까지 따른다.
  - Claude Code: Skill 도구로 `make-release`(플러그인 설치면 `rhyme-skills:make-release`)를 위 인자와 함께 호출한다.
  - 그 밖의 에이전트: 이 스킬 폴더의 형제 `../make-release/SKILL.md`를 읽고 그 절차대로 한다.
- 결과를 셋 중 하나로 정한다.
  - **완료**: 릴리즈가 공개됐다(URL 확인).
  - **할 것 없음**: 직전 태그 이후 변경이 없어 릴리즈를 건너뛰었다.
  - **중단**: make-release의 "멈출 때" 조건(기본 브랜치 아님, 비밀 값·정체불명 파일, 새 검증 실패, 충돌, 같은 태그 존재, 릴리즈 도구 충돌)이나 워크플로 빌드 실패를 고치지 못했다.

## 2. show-dev 실행
- **완료** 또는 **할 것 없음**이면 이어서 `show-dev` 스킬을 같은 방식으로(Claude Code는 Skill 도구 `show-dev`/`rhyme-skills:show-dev`, 그 밖은 `../show-dev/SKILL.md`) 불러 끝까지 따른다.
- **중단**이면 show-dev를 실행하지 않는다. 멈춘 이유와 재개 방법을 보고하고, 개발 서버만 따로 열려면 `/show-dev`를 쓰면 된다고 알린다.
- 순서대로 한다: Release 워크플로를 기다리는 동안 show-dev를 먼저 시작하지 않고, 릴리즈 노트 공개까지 끝난 뒤에 넘어간다.
- show-dev가 허용 호스트 설정을 소스에 추가하면 그 변경은 커밋하지 않는다(릴리즈에 섞이지 않게). 보고에 남긴다.

## 3. 보고
사용자 언어로 두 부분을 짧게 이어서:
1. 릴리즈 — make-release 7단계 보고(버전 직전 → 새, 바꾼 버전 파일, 변경 요약, 검증·워크플로 결과, 산출물, 릴리즈 URL, 주의점). 건너뛰었거나 중단했으면 그 이유.
2. 개발 서버 — show-dev 5단계 보고(localhost·LAN·Tailscale 주소, 바꾼 파일, 검증 결과, 로그 경로·종료 방법). 실행하지 않았으면 그 이유.
