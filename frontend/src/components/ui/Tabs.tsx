import { useState, createContext, useContext } from 'react'
import { cn } from '@/lib/utils'

interface TabsContextType {
  value: string
  onChange: (value: string) => void
}

const TabsContext = createContext<TabsContextType | undefined>(undefined)

function useTabs() {
  const context = useContext(TabsContext)
  if (!context) throw new Error('Tabs components must be used within Tabs')
  return context
}

export function Tabs({
  defaultValue,
  value,
  onValueChange,
  children,
}: {
  defaultValue?: string
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
}) {
  const [internalValue, setInternalValue] = useState(defaultValue || '')
  const currentValue = value !== undefined ? value : internalValue

  return (
    <TabsContext.Provider
      value={{
        value: currentValue,
        onChange: (v) => {
          setInternalValue(v)
          onValueChange?.(v)
        },
      }}
    >
      {children}
    </TabsContext.Provider>
  )
}

export function TabsList({ className, children }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('inline-flex h-9 items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground', className)}>
      {children}
    </div>
  )
}

export function TabsTrigger({ value, className, children }: { value: string } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const tabs = useTabs()
  return (
    <button
      onClick={() => tabs.onChange(value)}
      className={cn(
        'inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1 text-sm font-medium transition-all',
        tabs.value === value
          ? 'bg-background text-foreground shadow-sm'
          : 'hover:bg-muted/50 hover:text-foreground',
        className
      )}
    >
      {children}
    </button>
  )
}

export function TabsContent({ value, className, children }: { value: string } & React.HTMLAttributes<HTMLDivElement>) {
  const tabs = useTabs()
  if (tabs.value !== value) return null
  return <div className={cn('mt-2', className)}>{children}</div>
}
