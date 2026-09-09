# 복원력 확장 결정 질문 (Resiliency Extension Decision Questions)

복원력(Resiliency) 확장을 적용하기로 하셨습니다(Q11=A). 이 확장은 **아키텍처/프로세스 결정을 AI가 임의로 정하지 않고 사용자가 선택**하도록 규정합니다. 아래는 **Requirements 단계에서 반드시 확정**해야 하는 결정 사항입니다 (RESILIENCY-02, -03, -15).

> 참고: 이 프로젝트는 로컬 데모/MVP(Q5=A, Q6=A)로 설정되어 있습니다. 따라서 대부분 **가장 가벼운 옵션**이 자연스럽지만, 결정은 여러분의 몫입니다. 나머지 복원력 결정(CI/CD·롤백·배포 방식(RESILIENCY-04), 리전 토폴로지(RESILIENCY-08), 복원력 테스트(RESILIENCY-14))은 이후 **NFR Design** 단계에서 질문합니다.

각 `[Answer]:` 태그 뒤에 선택지 문자를 채우고, 완료되면 "완료"라고 알려주세요.

---

## Question R1: RTO/RPO 목표 및 재해 복구(DR) 전략 (RESILIENCY-02)
복구 시간 목표(RTO)와 복구 지점 목표(RPO)는 무엇인가요? 이 답변이 DR 전략과 인프라 이중화 수준을 결정합니다.

A) RPO/RTO: 시간(hours) 단위 — Backup & Restore 전략. 최저 비용($). 데이터만 백업, 서비스 미배포. 장애 시 IaC로 재배포 + 백업 복원. 비크리티컬 워크로드에 적합.

B) RPO/RTO: 수십 분 — Pilot Light 전략. 비용 $$. 데이터는 라이브, 서비스는 유휴. 장애 시 스케일업.

C) RPO/RTO: 분(minutes) 단위 — Warm Standby 전략. 비용 $$$. 데이터 라이브, 서비스 축소 운영 후 장애 시 스케일업.

D) RPO/RTO: near real-time — Multi-site Active/Active. 최고 비용($$$$). 다중 리전 동시 라이브. 미션 크리티컬/무중단.

E) N/A — 단일 리전 배포로 충분, 교차 리전 DR 불필요. 단일 리전 내 멀티 존 가용성에 의존. (로컬 데모/MVP에 적합)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question R2: 변경 관리 프로세스 (RESILIENCY-03)
이 워크로드의 프로덕션 변경은 어떻게 관리되어야 하나요? AI-DLC는 프로세스를 새로 만들지 않고 여러분의 답변에 맞춥니다.

A) 기존 조직의 변경 관리 프로세스 사용 — 이름/도구를 [Answer] 뒤에 기재 (예: ServiceNow, Jira Change, 내부 CAB). AI-DLC가 이를 참조하고 산출물을 맞춤.

B) 아직 공식 프로세스 없음 — AI-DLC가 경량 변경 관리 프로세스(변경 기록 + 승인 + 롤백 노트)를 제안하도록 함.

C) N/A — 이 워크로드는 공식 변경 관리 대상에서 제외(예: 내부 도구/데모). 제외 사유 기록. (로컬 데모/MVP에 적합)

X) Other (please describe after [Answer]: tag below)

[Answer]: A (기존 조직 프로세스 사용 선택 — 구체적 도구/이름 미지정, 추후 제공 예정으로 기록)

## Question R3: 인시던트 대응 프로세스 (RESILIENCY-15)
이 워크로드의 프로덕션 인시던트는 어떻게 처리되나요?

A) 기존 인시던트 대응 프로세스 사용 — 참조를 [Answer] 뒤에 기재 (예: PagerDuty 런북, 내부 IR/온콜 프로세스). AI-DLC가 알림/런북을 맞춤.

B) 공식 프로세스 없음 — AI-DLC가 경량 인시던트 대응 및 오류 교정(COE) 프로세스를 제안하도록 함.

X) Other (please describe after [Answer]: tag below)

[Answer]: A (기존 인시던트 대응 프로세스 사용 선택 — 구체적 참조 미지정, 추후 제공 예정으로 기록)
