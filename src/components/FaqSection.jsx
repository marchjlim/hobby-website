import { ExpandableButton } from "./ExpandableButton"

const questions_and_answers = [
    {index: 1, question: "Are your kits authentic?", answer: "Yes, everything I sell is authentic unless otherwise stated."},
    {index: 2, question: "Do you actually build gunpla?", answer: "Yep, like you, I also enjoy plamo. I'm not just a seller."},
    {index: 3, question: "Are you able to do delivery?", answer: "Currently delivery is only via lalamove or grab express, as I do not have materials for other delivery services right now."},
    {index: 4, question: "Can you notify me on WhatsApp/Telegram when my preorder arrives?", answer: "Yes. In fact, this is the preferred form of communication now especially for pre-orders. Just give me your contact."},
    {index: 5, question: "I have multiple preorders that arrive on different months. Can I collect them together?", answer: "No. The kits take up space and I will not hold them. Please collect within the stipulated timeline."},
    {index: 6, question: "I want to preorder from you, can we arrange a meetup time when the item arrives?", answer: "I have a general schedule but cannot predict my availability. Usually I'd just arrange with buyers when the item arrives."},
    {index: 7, question: "Is the price negotiable?", answer: "Depends on the item, but generally no unless you are buying multiple items or are a regular customer."},
    {index: 8, question: "The price on your website is cheaper than carousell, so is that the final price?", answer: "Only if you initiate a conversation with me through telegram and maintain it that way. Once the conversation hits carousell, it is whatever the price is on carousell."}
]

export const FaqSection = () => {
    return <section id="faq" className="relative min-h-screen flex flex-col items-center justify-center px-4">
        <div className="container max-w-4xl mx-auto text-center z-10">
            <div className="space-y-6">
                <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
                    <span className="opacity-0 animate-fade-in">Frequently</span>
                    <span className="text-primary opacity-0 animate-fade-in-delay-1">{" "}asked</span>
                    <span className="text-gradient ml-2 opacity-0 animate-fade-in-delay-2">{" "}questions</span>
                </h1>

                <p className="text-lg md:text-xl text-muted-foreground max-2-2xl mx-auto opacity:0 animate-fade-in-delay-3">
                    Some questions I've been asked a few times over carousell or during meetups.
                </p>
                
                <div className="grid grid-rows-1 sm:grid-rows-2 lg:grid-rows-3 gap-6">
                    {questions_and_answers.map((item, key) => (
                        <div key={key}> 
                            <ExpandableButton title={item.index + ". " + item.question} 
                                              content={item.answer}
                            />
                        </div>
                    ))}
                </div>

            </div>
        </div>

    </section>
}