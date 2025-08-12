export const ContactSection = () => {

    return <section id="contact" className="py-24 relative bg-secondary/30">
        <div className="container max-w-5xl mx-auto">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 text-center">
                Get In <span className="text-primary">Touch</span>
            </h2>

            <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
                Have any questions, want to purchase something or want me to find a kit for you? 
                Contact me.
            </p>

            <div>
                <div className="space-y-8">
                    <h3 className="text-2-xl font-semibold mb-6"> Contact Information </h3>

                    <div className="space-y-6 flex flex-col items-center">
                        <div className="flex items-start space-x-4">
                            <div className="p-3 rounded-full bg-primary/10">
                                <img src="icons/Carousell-logo-square.png"
                                     className="h-6 w-6 rounded" />
                            </div>
                            <div>
                                <h4 className="font-medium"> Carousell</h4>
                                <a href="https://www.carousell.sg/u/plasticmethenjoyer/" target="_blank"
                                    className="text-muted-foreground hover:text-primary transition-colors">
                                    Plasticmethenjoyer
                                </a>
                            </div>
                            <div className="p-3 rounded-full bg-primary/10">
                                <img src="icons/Telegram-icon.png"
                                     className="h-6 w-6 rounded" />
                            </div>
                            <div>
                                <h4 className="font-medium"> Telegram</h4>
                                <a href="https://t.me/plasticmethenjoyer" target="_blank"
                                    className="text-muted-foreground hover:text-primary transition-colors">
                                    @Plasticmethenjoyer
                                </a>
                            </div>
                            <div className="p-3 rounded-full bg-primary/10">
                                <img src="icons/Telegram-icon.png"
                                     className="h-6 w-6 rounded" />
                            </div>
                            <div>
                                <h4 className="font-medium"> Telegram Channel</h4>
                                <a href="https://t.me/plasticmethenjoyergroup" target="_blank"
                                    className="text-muted-foreground hover:text-primary transition-colors">
                                    @Plasticmethenjoyergroup
                                </a>
                            </div>
                        </div>

                    </div>


                    
                </div>

                
            </div>
        </div>
        
    </section>
}