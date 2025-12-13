import { ReactNode, useEffect, useState } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Box, Alert, IconButton, useTheme, useMediaQuery } from '@mui/material'
import RestoreIcon from '@mui/icons-material/Restore'
import SettingsSection from './SettingsSection'

export interface SettingSection {
  id: string
  title: string
  description?: string
  icon?: ReactNode
  badge?: string | number
  content: ReactNode
  defaultExpanded?: boolean
}

interface DraggableSettingsProps {
  sections: SettingSection[]
  storageKey?: string
  expandedCard: string | null
  onExpandedChange: (cardId: string | null) => void
}

const DraggableSettings = ({ sections, storageKey = 'settings-order', expandedCard, onExpandedChange }: DraggableSettingsProps) => {
  const [orderedSections, setOrderedSections] = useState<SettingSection[]>(sections)
  const [hasCustomOrder, setHasCustomOrder] = useState(false)
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const isTablet = useMediaQuery(theme.breakpoints.down('lg'))

  // Load saved order from localStorage
  useEffect(() => {
    const savedOrder = localStorage.getItem(storageKey)
    if (savedOrder) {
      try {
        const orderIds = JSON.parse(savedOrder) as string[]
        const reordered = orderIds
          .map(id => sections.find(s => s.id === id))
          .filter(Boolean) as SettingSection[]

        // Add any new sections that weren't in saved order
        const newSections = sections.filter(s => !orderIds.includes(s.id))
        setOrderedSections([...reordered, ...newSections])
        setHasCustomOrder(true)
      } catch (error) {
        console.error('Failed to load settings order:', error)
        setOrderedSections(sections)
      }
    } else {
      setOrderedSections(sections)
    }
  }, [sections, storageKey])

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      const oldIndex = orderedSections.findIndex((s) => s.id === active.id)
      const newIndex = orderedSections.findIndex((s) => s.id === over.id)

      const items = arrayMove(orderedSections, oldIndex, newIndex)
      setOrderedSections(items)
      setHasCustomOrder(true)

      // Save to localStorage
      const orderIds = items.map(item => item.id)
      localStorage.setItem(storageKey, JSON.stringify(orderIds))
    }
  }

  const handleResetOrder = () => {
    setOrderedSections(sections)
    setHasCustomOrder(false)
    localStorage.removeItem(storageKey)
  }

  return (
    <Box>
      {hasCustomOrder && (
        <Alert
          severity="info"
          sx={{ mb: 2 }}
          action={
            <IconButton
              color="inherit"
              size="small"
              onClick={handleResetOrder}
              title="Reset to default order"
            >
              <RestoreIcon fontSize="small" />
            </IconButton>
          }
        >
          Cards have been reordered. Drag cards to customize the layout or click the restore icon to reset.
        </Alert>
      )}

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={orderedSections.map(s => s.id)} strategy={verticalListSortingStrategy}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: isMobile
                ? '1fr'
                : isTablet
                ? 'repeat(2, 1fr)'
                : 'repeat(3, 1fr)',
              gap: 2,
            }}
          >
            {orderedSections.map((section) => (
              <SortableSettingCard
                key={section.id}
                section={section}
                expanded={expandedCard === section.id}
                onExpandedChange={(expanded) => onExpandedChange(expanded ? section.id : null)}
              />
            ))}
          </Box>
        </SortableContext>
      </DndContext>
    </Box>
  )
}

// Sortable wrapper for settings sections
interface SortableSettingCardProps {
  section: SettingSection
  expanded: boolean
  onExpandedChange: (expanded: boolean) => void
}

const SortableSettingCard = ({ section, expanded, onExpandedChange }: SortableSettingCardProps) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: section.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
    <Box
      ref={setNodeRef}
      style={style}
      sx={{
        opacity: isDragging ? 0.5 : 1,
      }}
    >
      <SettingsSection
        id={section.id}
        title={section.title}
        description={section.description}
        icon={section.icon}
        badge={section.badge}
        defaultExpanded={section.defaultExpanded}
        expanded={expanded}
        onExpandedChange={onExpandedChange}
        dragHandleProps={{ ...attributes, ...listeners }}
      >
        {section.content}
      </SettingsSection>
    </Box>
  )
}

export default DraggableSettings
