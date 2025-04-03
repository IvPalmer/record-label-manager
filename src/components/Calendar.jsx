import React, { useState, useEffect } from 'react';
import { 
  getCalendarEvents,
  addCalendarEvent,
  updateCalendarEvent,
  deleteCalendarEvent
} from '../api/calendar';
import styles from './Calendar.module.css';

const Calendar = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [viewMode, setViewMode] = useState('grid');
  const [newEvent, setNewEvent] = useState({
    title: '',
    date: '',
    type: 'release',
    description: ''
  });
  const [currentDate, setCurrentDate] = useState(new Date());

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const data = await getCalendarEvents();
        setEvents(data);
      } catch (err) {
        setError('Failed to load calendar events');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewEvent(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const createdEvent = await addCalendarEvent(newEvent);
      setEvents(prev => [...prev, createdEvent]);
      setShowModal(false);
      setNewEvent({
        title: '',
        date: '',
        type: 'release',
        description: ''
      });
    } catch (err) {
      setError('Failed to create event');
      console.error(err);
    }
  };

  const changeMonth = (offset) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() + offset);
    setCurrentDate(newDate);
  };

  const renderMonthGrid = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const firstDay = new Date(year, month, 1).getDay();

    const days = [];
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className={styles.emptyDay}></div>);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const dayEvents = events.filter(event => event.date === dateStr);
      
      days.push(
        <div key={day} className={styles.calendarDay}>
          <div className={styles.dayNumber}>{day}</div>
          {dayEvents.map(event => (
            <div 
              key={event.id} 
              className={`${styles.dayEvent} ${styles[event.type]}`}
              title={event.title}
            >
              {event.title}
            </div>
          ))}
        </div>
      );
    }

    return days;
  };

  const renderEventList = () => {
    return (
      <ul className={styles.eventList}>
        {events.map(event => (
          <li key={event.id} className={`${styles.eventItem} ${styles[event.type]}`}>
            <div className={styles.eventDate}>
              {new Date(event.date).toLocaleDateString()}
            </div>
            <div className={styles.eventDetails}>
              <h3>{event.title}</h3>
              <p>{event.description}</p>
              <span className={styles[`${event.type}Badge`]}>
                {event.type.charAt(0).toUpperCase() + event.type.slice(1)}
              </span>
            </div>
          </li>
        ))}
      </ul>
    );
  };

  if (loading) return <div>Loading calendar...</div>;
  if (error) return <div>{error}</div>;

  return (
    <div className={styles.calendarContainer}>
      <div className={styles.calendarHeader}>
        <h2>Release Calendar</h2>
        <div className={styles.viewControls}>
          <button
            className={`${styles.viewButton} ${viewMode === 'grid' ? styles.active : ''}`}
            onClick={() => setViewMode('grid')}
          >
            Grid View
          </button>
          <button
            className={`${styles.viewButton} ${viewMode === 'list' ? styles.active : ''}`}
            onClick={() => setViewMode('list')}
          >
            List View
          </button>
          <button 
            className={styles.addButton}
            onClick={() => setShowModal(true)}
          >
            Add Event
          </button>
        </div>
      </div>

      {viewMode === 'grid' && (
        <div className={styles.monthNavigation}>
          <button 
            className={styles.navButton}
            onClick={() => changeMonth(-1)}
          >
            Prev
          </button>
          <h3 className={styles.monthTitle}>
            {currentDate.toLocaleString('default', { month: 'long' })} {currentDate.getFullYear()}
          </h3>
          <button 
            className={styles.navButton}
            onClick={() => changeMonth(1)}
          >
            Next
          </button>
        </div>
      )}

      {viewMode === 'grid' ? (
        <div className={styles.calendarGrid}>
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
            <div key={day} className={styles.dayHeader}>{day}</div>
          ))}
          {renderMonthGrid()}
        </div>
      ) : (
        renderEventList()
      )}

      {showModal && (
        <div className={styles.modalOverlay}>
          <div className={styles.modalContent}>
            <h3>Add New Event</h3>
            <form onSubmit={handleSubmit}>
              <div className={styles.formGroup}>
                <label>Title</label>
                <input
                  type="text"
                  name="title"
                  value={newEvent.title}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Date</label>
                <input
                  type="date"
                  name="date"
                  value={newEvent.date}
                  onChange={handleInputChange}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Type</label>
                <select
                  name="type"
                  value={newEvent.type}
                  onChange={handleInputChange}
                >
                  <option value="release">Release</option>
                  <option value="deadline">Deadline</option>
                </select>
              </div>
              <div className={styles.formGroup}>
                <label>Description</label>
                <textarea
                  name="description"
                  value={newEvent.description}
                  onChange={handleInputChange}
                />
              </div>
              <div className={styles.formActions}>
                <button type="button" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Calendar;
