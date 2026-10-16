/** The step's main button, full width, held at the bottom of the step. The page keeps it still while the step changes. */
export const StepFooter = ({ children }: { children: React.ReactNode }) => (
    <div data-slot="step-footer" className="mt-auto pt-4 [&>button]:w-full">
        {children}
    </div>
)
