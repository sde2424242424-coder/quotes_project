# ENG
# Quotes Management and Analysis System

## Overview
This project is a full-stack web application that demonstrates the complete workflow of modern web development:  
**data crawling → database → REST API → UI integration → analytics**

The system collects quotes from **quotes.toscrape.com**, stores them in a database, and provides tools to manage and analyze the data.

---

## Features

### Data Crawling
- Scrapes quotes by category (tag)
- Uses **BeautifulSoup**
- Collects up to 20 quotes per category

---

### Database
- Uses **SQLite**
- Stores structured data:
  - `text`
  - `author`
  - `category`

---

### Backend (FastAPI)
- Fully implemented REST API:
  - Create (POST)
  - Read (GET)
  - Update (PUT)
  - Delete (DELETE)
- Interactive documentation:
  - `/docs` (Swagger UI)

---

### Frontend (Gradio)
- Integrated with FastAPI via `mount_gradio_app`
- Modern UI (not just tables)
- Features:
  - Quote card UI
  - Random quote generator
  - Search & filtering
  - Category selection

---

### Data Analysis
- Word frequency analysis
- Category distribution
- Author statistics
- Quote length visualization

---

### Deployment
- Deployed on **Railway**
- Accessible via external URL (not localhost)

---

## Tech Stack
- Python
- FastAPI
- Gradio
- SQLite
- BeautifulSoup
- Matplotlib

---

## Project Structure
quotes_project/
│── crawler.py # Web scraping
│── crud.py # DB logic
│── database.py # DB connection
│── gradio_app.py # UI (Gradio)
│── main.py # FastAPI app
│── models.py # DB models
│── schemas.py # API schemas
│── quotes.db # SQLite DB
│── requirements.txt

---

## How to Run

```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload


# KOR
# 격언 관리 및 분석 시스템 (Quotes Management and Analysis System)

## 개요
본 프로젝트는 현대 웹 개발의 전체 흐름을 이해하기 위한 풀스택 웹 애플리케이션입니다.  
**데이터 크롤링 → 데이터베이스 → REST API → UI 통합 → 데이터 분석** 과정을 하나의 시스템으로 구현하였습니다.

본 시스템은 **quotes.toscrape.com**에서 격언 데이터를 수집하여 데이터베이스에 저장하고,  
이를 관리하고 분석할 수 있는 기능을 제공합니다.

---

## 주요 기능

### 데이터 크롤링
- 카테고리(tag) 기반 격언 수집
- **BeautifulSoup** 사용
- 카테고리별 최대 20개 데이터 수집

---

### 데이터베이스
- **SQLite** 사용
- 저장 구조:
  - `text` (격언 내용)
  - `author` (저자)
  - `category` (카테고리)

---

### 백엔드 (FastAPI)
- REST API 완전 구현:
  - 생성 (POST)
  - 조회 (GET)
  - 수정 (PUT)
  - 삭제 (DELETE)
- API 문서 자동 제공:
  - `/docs` (Swagger UI)

---

### 프론트엔드 (Gradio)
- FastAPI에 **Gradio mount** 방식으로 통합
- 테이블이 아닌 **카드 기반 UI** 적용
- 주요 기능:
  - 격언 카드 표시
  - 랜덤 격언 생성
  - 검색 및 필터링
  - 카테고리 선택

---

### 데이터 분석
- 단어 빈도 분석 (Word Count)
- 카테고리 분포 시각화
- 저자별 통계 분석
- 격언 길이 분포 분석

---

### 배포 (Deployment)
- **Railway**를 통해 배포
- Localhost가 아닌 외부 URL로 접근 가능

---

## 기술 스택
- Python
- FastAPI
- Gradio
- SQLite
- BeautifulSoup
- Matplotlib

---

## 프로젝트 구조

quotes_project/
│── crawler.py # 웹 크롤링
│── crud.py # DB 처리 로직
│── database.py # 데이터베이스 연결
│── gradio_app.py # UI (Gradio)
│── main.py # FastAPI 실행
│── models.py # 데이터 모델
│── schemas.py # API 스키마
│── quotes.db # SQLite 데이터베이스
│── requirements.txt

---

## 실행 방법

```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload
