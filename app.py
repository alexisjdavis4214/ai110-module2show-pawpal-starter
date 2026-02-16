from pawpal_system import Owner, Pet, Task, Scheduler, ScheduledTask
import streamlit as st
import pandas as pd

# --- Persistent session-state (Pattern A): create-or-reuse objects ---
# ensure a single Owner instance is kept across Streamlit reruns
st.session_state.setdefault("owner", Owner(owner_id="o1", name="Default Owner", daily_time_available=120))
# keep a dict of pets keyed by pet_id
st.session_state.setdefault("pets", {})
# convenience local refs
owner = st.session_state["owner"]
pets = st.session_state["pets"]

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

st.title("🐾 PawPal+")

st.markdown(
    """
**PawPal+** is a pet care planning assistant. It helps pet owners plan care tasks
for their pets based on constraints like time, priority, and preferences.
"""
)

st.divider()

# --- Setup section: Owner and Pet management ---
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    owner_name = st.text_input("Owner name", value=owner.name)
    owner.name = owner_name
with col2:
    daily_minutes = st.number_input(
        "Daily time available (minutes)",
        min_value=30,
        max_value=480,
        value=owner.daily_time_available,
        step=15
    )
    owner.update_time_available(int(daily_minutes))
with col3:
    st.metric("Pets", len(pets))

st.subheader("👥 Manage Pets")

col1, col2, col3, col4 = st.columns(4)
with col1:
    pet_name = st.text_input("Pet name", value="")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    activity_level = st.selectbox("Activity level", ["low", "med", "high"])
with col4:
    st.write("")  # spacing
    if st.button("➕ Add Pet"):
        if pet_name:
            if pet_name in pets:
                st.error(f"❌ Pet '{pet_name}' already exists.")
            else:
                new_id = f"pet-{len(pets)+1}"
                pets[pet_name] = Pet(
                    pet_id=new_id,
                    name=pet_name,
                    species=species,
                    age_years=1.0,
                    activity_level=activity_level,
                    owner=owner
                )
                st.success(f"✅ Added pet '{pet_name}'!")
                st.rerun()
        else:
            st.error("❌ Enter a pet name.")

# Display existing pets
if pets:
    st.write("**Your pets:**")
    for name, pet in pets.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"• **{pet.name}** - {pet.species.title()} ({pet.activity_level} activity)")
        with col2:
            if st.button(f"Remove {name}", key=f"remove-{name}"):
                del pets[name]
                st.rerun()
else:
    st.info("No pets yet. Add one to get started!")

st.divider()

# --- Task management section ---
st.subheader("📋 Manage Tasks")

if not pets:
    st.warning("Add a pet first to create tasks.")
else:
    selected_pet_name = st.selectbox("Select pet", list(pets.keys()))
    selected_pet = pets[selected_pet_name]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task name", value="")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=5, max_value=180, value=20, step=5)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)
    with col4:
        category = st.selectbox("Category", ["feed", "walk", "play", "grooming", "meds", "other"])
    
    if st.button("➕ Add Task"):
        if task_title:
            priority_map = {"low": 1, "medium": 3, "high": 5}
            pr = priority_map[priority]
            task_id = f"{selected_pet.pet_id}-task-{len(selected_pet.tasks) + 1}"
            task_obj = Task(
                task_id=task_id,
                name=task_title,
                category=category,
                duration=int(duration),
                priority=pr
            )
            selected_pet.add_task(task_obj)
            owner.tasks.append(task_obj)
            st.success(f"✅ Added task: {task_title}")
            st.rerun()
        else:
            st.error("❌ Enter a task name.")
    
    # Display tasks for selected pet
    if selected_pet.tasks:
        st.write(f"**Tasks for {selected_pet_name}:**")
        # Create a cleaner display using DataFrame
        task_data = []
        for t in selected_pet.tasks:
            task_data.append({
                "Task": t.name,
                "Category": t.category.title(),
                "Duration (min)": t.duration,
                "Priority": ["Low", "Medium", "High"][min(t.priority // 2, 2)],
                "Status": "✅ Done" if t.completed else "⏳ Pending"
            })
        st.table(task_data)
    else:
        st.info(f"No tasks yet for {selected_pet_name}. Add one above.")

st.divider()

# --- Scheduling and Plan Generation ---
st.subheader("📅 Generate Schedule")

if not pets:
    st.warning("Add a pet and tasks first.")
else:
    scheduler = Scheduler(explain=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 Generate Schedule"):
            st.session_state.show_schedule = True
    
    with col2:
        if st.button("Clear Schedule"):
            st.session_state.show_schedule = False
            st.rerun()
    
    if st.session_state.get("show_schedule", False):
        # Generate plans for all pets and collect conflicts
        all_scheduled = []
        total_conflicts = []
        
        for pet_name, pet in pets.items():
            if not pet.tasks:
                continue
            
            plan = scheduler.generate_plan(owner, pet, pet.tasks)
            scheduled = plan.get("scheduled", [])
            
            # Add pet_name to each scheduled task for conflict detection
            for s in scheduled:
                all_scheduled.append((pet_name, s))
            
            st.markdown(f"### {pet.name}'s Schedule")
            
            # --- Display scheduled tasks in a professional table ---
            if scheduled:
                scheduled_sorted = scheduler.sort_by_time(
                    [s.task for s in scheduled]
                )
                
                schedule_data = []
                for task in scheduled_sorted:
                    # Find corresponding ScheduledTask to get times
                    sched_task = next(
                        (s for s in scheduled if s.task.task_id == task.task_id),
                        None
                    )
                    if sched_task:
                        schedule_data.append({
                            "Time": f"{sched_task.start.strftime('%H:%M')} - {sched_task.end.strftime('%H:%M')}",
                            "Task": task.name,
                            "Category": task.category.title(),
                            "Duration": f"{task.duration} min",
                            "Priority": ["🔵 Low", "🟡 Medium", "🔴 High"][
                                min(task.priority // 2, 2)
                            ]
                        })
                
                if schedule_data:
                    st.success(f"✅ Scheduled {len(scheduled)} tasks")
                    st.dataframe(
                        pd.DataFrame(schedule_data),
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.info(f"No tasks scheduled for {pet_name}.")
            
            # --- Display skipped tasks with reasons ---
            skipped = plan.get("skipped", [])
            if skipped:
                st.warning(f"⚠️ Skipped {len(skipped)} tasks:")
                skipped_data = []
                for task, reason in skipped:
                    skipped_data.append({
                        "Task": task.name,
                        "Category": task.category.title(),
                        "Reason": reason
                    })
                st.dataframe(
                    pd.DataFrame(skipped_data),
                    use_container_width=True,
                    hide_index=True
                )
            
            # --- Display ranked/priority view ---
            with st.expander(f"📊 Task Priority Ranking for {pet_name}"):
                ranked = scheduler.rank_tasks(owner, pet, pet.tasks)
                rank_data = []
                for i, task in enumerate(ranked, 1):
                    score = scheduler.get_score_cached(task, owner, pet)
                    rank_data.append({
                        "Rank": i,
                        "Task": task.name,
                        "Score": f"{score:.1f}",
                        "Status": "✅" if task.completed else "⏳"
                    })
                st.dataframe(
                    pd.DataFrame(rank_data),
                    use_container_width=True,
                    hide_index=True
                )
        
        # --- CONFLICT DETECTION & WARNING ---
        if all_scheduled:
            conflicts = scheduler.detect_conflicts(all_scheduled)
            
            if conflicts:
                st.divider()
                st.markdown("### ⚠️ SCHEDULE CONFLICTS DETECTED")
                
                with st.container(border=True):
                    st.error(
                        f"**{len(conflicts)} conflict(s) found!** These tasks overlap and cannot both happen."
                    )
                    
                    for conflict_msg in conflicts:
                        st.warning(f"🔴 {conflict_msg}")
                    
                    st.markdown(
                        """
                        **How to resolve:**
                        1. **Reduce task duration** - adjust how long a task takes
                        2. **Lower priority tasks** - skip less important tasks
                        3. **Increase owner availability** - allocate more time if possible
                        4. **Adjust preferred windows** - reschedule tasks to different times
                        """
                    )
            else:
                st.success(
                    f"✅ **No conflicts!** All {len(all_scheduled)} tasks fit perfectly."
                )
        
        # --- Display explanation ---
        if plan.get("explanation"):
            with st.expander("📝 Scheduling Explanation"):
                for line in plan["explanation"]:
                    st.write(line)

st.divider()

with st.expander("ℹ️ About PawPal+"):
    st.markdown(
        """
        **PawPal+** helps you build an organized care schedule for your pets.
        
        **Features:**
        - 🐾 Multi-pet management
        - 📋 Task prioritization based on importance and constraints
        - ⏰ Intelligent scheduling that respects time availability
        - ⚠️ Automatic conflict detection and warnings
        - 📊 Priority ranking to understand which tasks matter most
        """
    )

