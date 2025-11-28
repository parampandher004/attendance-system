--
-- PostgreSQL database dump
--

\restrict 4CgNSj6fu3FiLXb3NgheKgSgiMX0VmHtrg80KhtkprWHe3hFSmlnpgNzQh22Ahc

-- Dumped from database version 17.6 (Debian 17.6-2.pgdg13+1)
-- Dumped by pg_dump version 17.6 (Debian 17.6-2.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: classes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.classes (id, name) FROM stdin;
1	BTECH 7th SEM 2025
\.


--
-- Data for Name: subjects; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.subjects (id, name, code) FROM stdin;
1	Internet of Things	CSEL 711
2	Algorithm Graph Theory	CSEL 721
3	Principles of Artificial Intelligence	CSEL 731
4	Internet of Things (Laboratory)	CSEP 711
5	Algorithm Graph Theory (Laboratory)	CSEP 721
6	Artificial Intelligence (Laboratory)	CSEP 731
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, password, role) FROM stdin;
1	parampandher01	5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8	student
2	anirban_ghosh	5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8	teacher
3	arindam_sen	5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8	teacher
4	priyanka_roy	5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8	teacher
5	tanushree_m	5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8	teacher
6	gourav_biswas	5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8	student
7	admin	5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8	admin
8	tushar_kanti	5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8	student
9	diptendu_chatterjee	5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8	student
10	souryadipta_paul	5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8	student
\.


--
-- Data for Name: teachers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.teachers (id, name, user_id) FROM stdin;
1	Anirban Ghosh	2
2	Arindam Sen	3
3	Priyanka Roy	4
5	Tanushree Mukherjee	5
\.


--
-- Data for Name: teachersubjects; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.teachersubjects (id, teacher_id, subject_id, class_id) FROM stdin;
1	1	1	1
2	3	2	1
3	5	3	1
4	2	4	1
5	3	5	1
6	5	6	1
\.


--
-- Data for Name: periods; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.periods (id, start_time, end_time, date, day, teacher_subject_id, is_manual, status) FROM stdin;
1	10:30:00	12:00:00	2025-11-11	2	2	0	completed
2	13:00:00	14:30:00	2025-11-11	2	3	0	completed
3	10:30:00	12:00:00	2025-11-11	2	2	0	completed
4	13:00:00	14:30:00	2025-11-11	2	3	0	completed
10	16:00:00	18:00:00	2025-11-20	4	3	0	completed
9	16:00:00	18:00:00	2025-11-20	4	2	0	completed
5	15:00:00	18:00:00	2025-11-18	2	3	0	scheduled
6	22:00:00	23:00:00	2025-11-18	2	6	0	running
7	13:00:00	16:00:00	2025-11-19	3	3	0	completed
8	12:00:00	14:00:00	2025-11-19	3	1	0	completed
\.


--
-- Data for Name: students; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.students (id, name, roll_no, class_id, user_id, folder_id) FROM stdin;
1	Paramveer Singh Pandher	3	1	1	1qAY7qHiC6dZ0g4uAxkd8jF7tNNEXZTTH
3	Tushar Kanti	5	1	8	1kmaGRKLMv-LHxZ9gxDnhWrq-xdgSpuQH
2	Gourav Biswas	1	1	6	1Yhtt4-Kw64PxCfvpFz05LlAVLJatm3oW
4	Diptendu Chatterjee	2	1	9	1E6gDw-GNY3DY74w-Q14EiIpNKBGiXbhr
5	Souryadipta Paul	4	1	10	1eGViwnMqkb5elpy0DaTJJ75FAG2Y8RvV
\.


--
-- Data for Name: attendance; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.attendance (id, student_id, period_id, status) FROM stdin;
13	1	2	present
41	1	7	present
\.


--
-- Data for Name: students_images; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.students_images (id, student_id, drive_file_id, file_name, uploaded_at) FROM stdin;
1	1	1S3qtXM9qKu90NrPJ5g4rk7P1SQVI4BYO	drawing.png	2025-11-26 14:07:56.373954
2	1	1zHEA6g5oQoXxdpIY4_P2qtBh6w25HwTP	drawing.png	2025-11-26 14:08:49.528739
3	1	1u5lsQrf2zsRv8CoFGBYiAdbxJ435D3Oc	face.jpg	2025-11-26 15:02:26.559708
4	1	1OpEWkW4HY_P9UVOAsMfCq2OvB-oShHIH	g1.png	2025-11-26 15:04:26.733974
5	2	1tX1A9OumAhjBAXooIXCjWMOaCbMp_tcu	face.jpg	2025-11-28 19:36:37.771892
\.


--
-- Data for Name: students_embeddings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.students_embeddings (id, image_id, vector, created_at) FROM stdin;
\.


--
-- Data for Name: weekly_periods; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.weekly_periods (id, teacher_subject_id, day, start_time, end_time) FROM stdin;
1	3	1	15:00:00	16:30:00
2	2	2	10:30:00	12:00:00
3	3	2	13:00:00	14:30:00
4	2	4	11:00:00	13:00:00
5	1	6	11:30:00	13:00:00
6	4	6	14:00:00	16:00:00
\.


--
-- Name: attendance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.attendance_id_seq', 41, true);


--
-- Name: classes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.classes_id_seq', 1, false);


--
-- Name: periods_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.periods_id_seq', 10, true);


--
-- Name: students_embeddings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.students_embeddings_id_seq', 1, false);


--
-- Name: students_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.students_id_seq', 5, true);


--
-- Name: students_images_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.students_images_id_seq', 5, true);


--
-- Name: subjects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.subjects_id_seq', 6, true);


--
-- Name: teachers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.teachers_id_seq', 6, true);


--
-- Name: teachersubjects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.teachersubjects_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 10, true);


--
-- Name: weekly_periods_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.weekly_periods_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

\unrestrict 4CgNSj6fu3FiLXb3NgheKgSgiMX0VmHtrg80KhtkprWHe3hFSmlnpgNzQh22Ahc

