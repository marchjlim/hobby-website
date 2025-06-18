import { Pencil } from "lucide-react"


export const EditListingButton = ({ onEdited }) => {
    return <button className="relative group" onClick={onEdited}>
                <Pencil />
                <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block 
                                bg-black text-white text-xs rounded px-2 py-1 z-10 whitespace-nowrap">
                    Edit listing
                </span>
            </button>
    
}