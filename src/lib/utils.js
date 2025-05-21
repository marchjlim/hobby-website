import {clsx} from 'clsx'
import { twMerge } from 'tailwind-merge'

export const cn = (...inputs) => {
    // combine classnames without writing lots of lines in one line
    return twMerge(clsx(inputs));

}