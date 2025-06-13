import { Pencil } from "lucide-react"
import { supabase } from "../supabase-client"


export const EditListingButton = ({ listing, onEdited }) => {
    // const deleteListing = async (listingId) => {
    //     const {error} = await supabase.from("Listings").delete().eq("id", listingId);
    //     if (error) {
    //         console.error("Error deleting listing:", error.message);
    //         return;
    //     } 
    //     if (onDeleted) {
    //         onDeleted();
    //     }
    // }
    return <button className="relative group" onClick={onEdited}>
                <Pencil />
                <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block 
                                bg-black text-white text-xs rounded px-2 py-1 z-10 whitespace-nowrap">
                    Edit listing
                </span>
            </button>
    
}