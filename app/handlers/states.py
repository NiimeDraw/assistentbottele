"""Definisi FSM States (finite state machine) untuk alur input multi-step."""
from aiogram.fsm.state import State, StatesGroup


class TaskStates(StatesGroup):
    waiting_title = State()
    waiting_deadline = State()
    waiting_description = State()


class ScheduleStates(StatesGroup):
    waiting_mata_kuliah = State()
    waiting_hari = State()
    waiting_jam_mulai = State()
    waiting_jam_selesai = State()
    waiting_ruangan = State()
    waiting_dosen = State()
    waiting_reminder = State()


class ScheduleEditStates(StatesGroup):
    waiting_mata_kuliah = State()
    waiting_jam_mulai = State()
    waiting_jam_selesai = State()
    waiting_ruangan = State()
    waiting_dosen = State()


class NoteStates(StatesGroup):
    waiting_title = State()
    waiting_content = State()


class AIStates(StatesGroup):
    waiting_question = State()


class UserStates(StatesGroup):
    waiting_fakultas = State()
    waiting_jurusan = State()
    waiting_angkatan = State()
    waiting_semester = State()
    confirm_delete = State()

class AcademicStates(StatesGroup):
    waiting_title = State()
    waiting_type = State()
    waiting_start_date = State()
    waiting_end_date = State()
    waiting_location = State()
    waiting_description = State()
    waiting_reminder_days = State()
    waiting_search_keyword = State()


class NilaiStates(StatesGroup):
    waiting_mata_kuliah = State()
    waiting_sks = State()
    waiting_nilai = State()
    waiting_semester = State()
    waiting_target_ipk = State()
    waiting_sisa_sks = State()
    waiting_prediksi_data = State()