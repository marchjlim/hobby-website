import { useState } from "react"
import { DeleteTagButton } from "./DeleteTagButton"
import { EditTagButton } from "./EditTagButton"
import { EditTagForm } from "./EditTagForm";


export const TagManagementCard = ({ tag, onTagUpdate }) => {
    const [isEditting, setIsEditting] = useState(false);
    
    return (isEditting ? <EditTagForm tagName={tag} onTagEdited={()=>{
                                                                        onTagUpdate();
                                                                        setIsEditting(false);
                                                                     }} 
                                                    onCancel={() => setIsEditting(false)} />
                       : <span
                className="tag bg-primary text-primary-foreground flex items-center gap-2"
            >
                {tag}
                <EditTagButton tagName={tag} onEdited={() => setIsEditting(true)}/>
                <DeleteTagButton tagName={tag} onDeleted={onTagUpdate}/>
            </span>)
}