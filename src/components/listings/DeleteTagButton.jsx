import { Trash } from "lucide-react"
import { authenticatedFetch } from "@/lib/authenticated-fetch"


export const DeleteTagButton = ({ tagName, onDeleted }) => {
    const deleteTag = async () => {

        const usageResponse = await fetch(
            `/api/listings/tags/${encodeURIComponent(tagName)}/usage`,
        );
        if (!usageResponse.ok) {
            console.error("Error fetching tag usage:", usageResponse.status);
            return;
        }
        const { count } = await usageResponse.json();

        if (count > 0) {
            if (!window.confirm(`This tag is used in ${count} listing(s). Delete anyway?`)) {
                return;
            }
        }

        const response = await authenticatedFetch(
            `/api/listings/tags/${encodeURIComponent(tagName)}`,
            { method: "DELETE" },
        );
        if (!response.ok) {
            console.error("Error deleting tag:", response.status);
            return;
        }
        if (onDeleted) {
            onDeleted();
        }
    }
    
    return <button className="relative group" onClick={() => {
                                                                if (window.confirm("Delete tag?")) {
                                                                    deleteTag();
                                                                }
                                                                
                                                            }}>
                <Trash className="text-red-500"/>
                <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block 
                                bg-black text-white text-xs rounded px-2 py-1 z-10 whitespace-nowrap">
                    Delete tag
                </span>
            </button>
    
}
