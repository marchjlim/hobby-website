import { Pencil } from "lucide-react"


export const EditTagButton = ({ tagName, onEdited}) => {

    const editTag = async () => {
        const { count } = await supabase
                                .from("Tagged")
                                .select("*", { count: "exact", head: true })
                                .eq("TagName", tagName);

        if (count > 0) {
            if (!window.confirm(`This tag is used in ${count} listing(s). Delete anyway?`)) {
                return;
            }
            // delete relations
            const { error } = await supabase.from("Tagged").delete().ilike("TagName", tagName);
            if (error) {
                console.log("Error deleting tag relation:", error.message);
                return;
            }
        }

        const { error } = await supabase.from("ListingTag").delete().ilike("name", tagName);
        if (error) {
            console.error("Error deleting tag:", error.message);
            return;
        }
        if (onDeleted) {
            onDeleted();
        }
    }
    
    return <button className="relative group" onClick={() => onEdited()}>
                <Pencil />
                <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block 
                                bg-black text-white text-xs rounded px-2 py-1 z-10 whitespace-nowrap">
                    Edit tag
                </span>
            </button>
    
}