import { useMemo } from 'react'
import * as dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import advancedFormat from 'dayjs/plugin/advancedFormat'
import useSiteContext from './useSiteContext'

dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.extend(advancedFormat)

//// Neoffice - 24-hour clock (a4eb3b921, 2026-01-06 "fix: Use 24-hour time format instead of 12-hour AM/PM"): the format union loses its AM/PM members.
type DateFormatOptions = 'Do MMMM YYYY, HH:mm' | 'Do MMMM [at] HH:mm' | 'HH:mm' | 'hh:mm'

/**
 * Hook to format a date string based on the format option
 * @param timestamp - The date string to format
 * @param format - The format option to use
 * @returns The formatted date string
 */
//// Neoffice - 24-hour clock (a4eb3b921, 2026-01-06 "fix: Use 24-hour time format instead of 12-hour AM/PM"): default format for every date shown in the app.
const useDateFormat = (timestamp: string, format: DateFormatOptions | string = 'Do MMMM YYYY, HH:mm') => {

  const siteInformation = useSiteContext()

  const SYSTEM_TIMEZONE = siteInformation?.system_timezone ?? 'Asia/Kolkata'

  const formattedDate = useMemo(() => {

    return dayjs.tz(timestamp, SYSTEM_TIMEZONE).local().format(format)

  }, [timestamp, format, SYSTEM_TIMEZONE])

  return formattedDate

}

export default useDateFormat