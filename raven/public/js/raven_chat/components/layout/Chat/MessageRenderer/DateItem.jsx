//// Neoffice — added file (no upstream equivalent): part of the desk chat widget that upstream removed in 3.1 (#2311) and we keep, the Synk icon of the cockpit opens it. Goes away with the widget.
import React from 'react'

const DateItem = ({ date }) => {
    return (
        <div className='raven-date-separator'>
            <div className='raven-date-separator-line'>

            </div>
            <div className='raven-date-separator-text'>
                {moment(date, frappe.defaultDatetimeFormat).format('Do MMMM YYYY')}
            </div>
            <div className='raven-date-separator-line'></div>
        </div>
    )
}

export default DateItem