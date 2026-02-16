from pawpal_system import Owner, Pet, Task, Scheduler
import streamlit as st

# --- Persistent session-state (Pattern A): create-or-reuse objects ---
# ensure a single Owner instance is kept across Streamlit reruns
st.session_state.setdefault("owner", Owner(owner_id="o1", name="Default Owner", daily_time_available=120))
# keep a dict of pets keyed by pet_id
st.session_state.setdefault("pets", {})
# convenience local refs
owner = st.session_state["owner"]
pets = st.session_state["pets"]

# keep owner name and pet creation in sync with UI
owner.name = owner_name
# create or reuse pet by displayed name
if pet_name:
    if pet_name not in pets:
        new_id = f"pet-{len(pets)+1}"
        pets[pet_name] = Pet(pet_id=new_id, name=pet_name, species=species, age_years=1.0, activity_level="med", owner=owner)
selected_pet = pets.get(pet_name)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

# Add pet button (calls our Pet constructor and stores in session-state)
if st.button("Add pet"):
    if pet_name:
        if pet_name in pets:
            st.info(f"Pet '{pet_name}' already exists.")
        else:
            new_id = f"pet-{len(pets)+1}"
            pets[pet_name] = Pet(pet_id=new_id, name=pet_name, species=species, age_years=1.0, activity_level="med", owner=owner)
            st.success(f"Added pet '{pet_name}'")
    else:
        st.error("Enter a pet name before adding.")

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    # keep the lightweight UI task list for display
    st.session_state.tasks.append(
        {"title": task_title, "duration_minutes": int(duration), "priority": priority}
    )
    # also persist a Task object into the selected pet and the owner
    # ensure pet exists in session-state
    selected_pet = pets.get(pet_name)
    # map priority string to numeric
    priority_map = {"low": 1, "medium": 3, "high": 5}
    pr = priority_map.get(priority, 3)
    if selected_pet:
        tid = f"{selected_pet.pet_id}-t{len(selected_pet.tasks)+1}"
        task_obj = Task(task_id=tid, name=task_title, category="general", duration=int(duration), priority=pr)
        selected_pet.add_task(task_obj)
        owner.tasks.append(task_obj)

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    if not selected_pet:
        st.error("No pet selected to schedule for. Add or select a pet first.")
    else:
        scheduler = Scheduler(explain=True)
        plan = scheduler.generate_plan(owner, selected_pet, list(selected_pet.tasks))
        scheduled = plan.get("scheduled", [])
        skipped = plan.get("skipped", [])
        if scheduled:
            st.markdown("### Scheduled")
            for s in scheduled:
                st.write(f"{selected_pet.name}: {s.task.name} ({s.task.category}) — {s.start.strftime('%H:%M')} to {s.end.strftime('%H:%M')}")
        if skipped:
            st.markdown("### Skipped")
            for t, reason in skipped:
                st.write(f"{t.name}: {reason}")
        if plan.get("explanation"):
            st.markdown("### Explanation")
            for line in plan["explanation"]:
                st.write(line)
