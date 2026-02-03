import { Building2, Briefcase, GraduationCap, FlaskConical } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'

const organizationTypes = [
  {
    id: 'tto',
    label: 'Technology Transfer Office',
    description: 'University or research institution commercializing research',
    icon: GraduationCap,
  },
  {
    id: 'vc',
    label: 'Venture Capital',
    description: 'Investing in deep-tech and science-based startups',
    icon: Briefcase,
  },
  {
    id: 'corporate',
    label: 'Corporate Innovation',
    description: 'Scouting research for internal R&D or partnerships',
    icon: Building2,
  },
  {
    id: 'research',
    label: 'Research Organization',
    description: 'Academic lab or research institute',
    icon: FlaskConical,
  },
]

interface OrganizationStepProps {
  value: string
  onChange: (type: string) => void
  onNext: () => void
}

export function OrganizationStep({ value, onChange, onNext }: OrganizationStepProps): JSX.Element {
  return (
    <div className="space-y-6">
      <p className="text-center text-muted-foreground">
        Select your organization type to customize your experience
      </p>

      <div className="grid gap-4 md:grid-cols-2">
        {organizationTypes.map((type) => {
          const Icon = type.icon
          const isSelected = value === type.id

          return (
            <button
              key={type.id}
              onClick={() => onChange(type.id)}
              className={cn(
                'flex items-start gap-4 p-4 rounded-lg border-2 text-left transition-all',
                isSelected
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:border-primary/50 hover:bg-muted/50'
              )}
            >
              <div
                className={cn(
                  'flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center',
                  isSelected ? 'bg-primary text-primary-foreground' : 'bg-muted'
                )}
              >
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-medium">{type.label}</h3>
                <p className="text-sm text-muted-foreground mt-1">{type.description}</p>
              </div>
            </button>
          )
        })}
      </div>

      <div className="flex justify-center pt-4">
        <Button onClick={onNext} disabled={!value} size="lg">
          Continue
        </Button>
      </div>
    </div>
  )
}
