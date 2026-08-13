import { Trash } from "lucide-react"
import { authenticatedFetch } from "@/lib/authenticated-fetch"


export const DeleteListingButton = ({ listing, onDeleted }) => {
    const deleteListing = async (listingId) => {
        const response = await authenticatedFetch(`/api/listings/${listingId}`, {
            method: "DELETE",
        });
        if (!response.ok) {
            console.error("Error deleting listing:", response.status);
            return;
        } 
        if (onDeleted) {
            onDeleted();
        }
    }
    return <button className="relative group" onClick={() => {
                                                                if (window.confirm("Delete listing?")) {
                                                                    deleteListing(listing.id);
                                                                }
                                                                
                                                            }}>
                <Trash className="text-red-500"/>
                <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block 
                                bg-black text-white text-xs rounded px-2 py-1 z-10 whitespace-nowrap">
                    Delete listing
                </span>
            </button>
    
}
