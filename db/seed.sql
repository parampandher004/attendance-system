--
-- PostgreSQL database dump
--


-- Dumped from database version 17.6
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

INSERT INTO public.classes VALUES (1, 'BTECH 7th SEM 2025');


--
-- Data for Name: subjects; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.subjects VALUES (1, 'Internet of Things', 'CSEL 711');
INSERT INTO public.subjects VALUES (2, 'Algorithm Graph Theory', 'CSEL 721');
INSERT INTO public.subjects VALUES (3, 'Principles of Artificial Intelligence', 'CSEL 731');
INSERT INTO public.subjects VALUES (4, 'Internet of Things (Laboratory)', 'CSEP 711');
INSERT INTO public.subjects VALUES (5, 'Algorithm Graph Theory (Laboratory)', 'CSEP 721');
INSERT INTO public.subjects VALUES (6, 'Artificial Intelligence (Laboratory)', 'CSEP 731');


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.users VALUES (1, 'parampandher01', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'student');
INSERT INTO public.users VALUES (2, 'anirban_ghosh', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'teacher');
INSERT INTO public.users VALUES (3, 'arindam_sen', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'teacher');
INSERT INTO public.users VALUES (4, 'priyanka_roy', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'teacher');
INSERT INTO public.users VALUES (5, 'tanushree_m', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'teacher');


--
-- Data for Name: teachers; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.teachers VALUES (1, 'Anirban Ghosh', 2);
INSERT INTO public.teachers VALUES (2, 'Arindam Sen', 3);
INSERT INTO public.teachers VALUES (3, 'Priyanka Roy', 4);
INSERT INTO public.teachers VALUES (5, 'Tanushree Mukherjee', 5);


--
-- Data for Name: teachersubjects; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.teachersubjects VALUES (1, 1, 1, 1);
INSERT INTO public.teachersubjects VALUES (2, 3, 2, 1);
INSERT INTO public.teachersubjects VALUES (3, 5, 3, 1);
INSERT INTO public.teachersubjects VALUES (4, 2, 4, 1);
INSERT INTO public.teachersubjects VALUES (5, 3, 5, 1);
INSERT INTO public.teachersubjects VALUES (6, 5, 6, 1);


--
-- Data for Name: periods; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: students; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.students VALUES (1, 'Paramveer Singh Pandher', '3', 1, 1);


--
-- Data for Name: attendance; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: face_encodings; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: weekly_periods; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.weekly_periods VALUES (1, 3, 1, '15:00:00', '16:30:00');
INSERT INTO public.weekly_periods VALUES (2, 2, 2, '10:30:00', '12:00:00');
INSERT INTO public.weekly_periods VALUES (3, 3, 2, '13:00:00', '14:30:00');
INSERT INTO public.weekly_periods VALUES (4, 2, 4, '11:00:00', '13:00:00');
INSERT INTO public.weekly_periods VALUES (5, 1, 6, '11:30:00', '13:00:00');
INSERT INTO public.weekly_periods VALUES (6, 4, 6, '14:00:00', '16:00:00');


--
-- Name: attendance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.attendance_id_seq', 12, true);


--
-- Name: students_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.students_id_seq', 1, true);


--
-- Name: subjects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.subjects_id_seq', 6, true);


--
-- Name: teachers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.teachers_id_seq', 5, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 5, true);


--
-- PostgreSQL database dump complete
--
