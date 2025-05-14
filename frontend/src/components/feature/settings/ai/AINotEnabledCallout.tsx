import { CustomCallout } from "@/components/common/Callouts/CustomCallout"
import useRavenSettings from "@/hooks/fetchers/useRavenSettings"
import { Link as RadixLink, Text } from "@radix-ui/themes"
import { BiInfoCircle } from "react-icons/bi"
import { Link } from "react-router-dom"

const AINotEnabledCallout = () => {

    const { ravenSettings } = useRavenSettings()

    if (ravenSettings?.enable_ai_integration === 1) {
        return null
    }

    return (
        <CustomCallout
            iconChildren={<BiInfoCircle size='18' />}
            rootProps={{ color: 'blue', variant: 'surface' }}
            textChildren={<Text>Raven AI is not enabled. Please enable it in <RadixLink asChild color='blue' underline='always'><Link to='/settings/llm-settings'>LLM Settings</Link></RadixLink></Text>}
        />
    )
}

export default AINotEnabledCallout