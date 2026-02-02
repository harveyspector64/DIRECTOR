import { useMemo } from 'react';
import Timeline, { TimelineGroupBase, TimelineItemBase } from 'react-calendar-timeline';
import 'react-calendar-timeline/lib/Timeline.css';
import { Director, ProjectEvent } from '../lib/types';

interface DirectorTimelineProps {
  directors: Director[];
  events: ProjectEvent[];
  onSelectDirector: (directorId: string) => void;
}

export function DirectorTimeline({ directors, events, onSelectDirector }: DirectorTimelineProps) {
  const groups: TimelineGroupBase[] = useMemo(
    () =>
      directors.map((director) => ({
        id: director.id,
        title: director.name
      })),
    [directors]
  );

  const items: TimelineItemBase[] = useMemo(() => {
    return events
      .filter((event) => directors.some((director) => director.id === event.director_id))
      .map((event) => {
        const start = event.dates?.start ? new Date(event.dates.start) : new Date(event.last_verified);
        const end = event.dates?.end ? new Date(event.dates.end) : new Date(start.getTime() + 1000 * 60 * 60 * 24 * 30);
        return {
          id: event.id,
          group: event.director_id,
          title: event.project_title,
          start_time: start,
          end_time: end
        };
      });
  }, [events, directors]);

  return (
    <div className="timeline">
      <Timeline
        groups={groups}
        items={items}
        lineHeight={36}
        itemHeightRatio={0.75}
        stackItems
        defaultTimeStart={new Date(new Date().setMonth(new Date().getMonth() - 3))}
        defaultTimeEnd={new Date(new Date().setMonth(new Date().getMonth() + 9))}
        onItemSelect={(itemId) => {
          const item = items.find((event) => event.id === itemId);
          if (item) {
            onSelectDirector(String(item.group));
          }
        }}
        onCanvasClick={(groupId) => {
          if (groupId) {
            onSelectDirector(String(groupId));
          }
        }}
      />
    </div>
  );
}
