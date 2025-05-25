import { Code, ShoppingCart, Wrench } from "lucide-react"

export const AboutSection = () => {
    return <section id="about" className="py-24 px-4 relative">
        {" "}
        <div className="container mx-auto max-w-5xl">
            <h2 className="text-3xl md:text-4xl font-bold mb-12 text-center">
                About <span className="text-primary"> Me</span>
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items center">
                <div className="space-y-6">
                    <h3 className="text-2xl font-semibold">
                        Full-time student, part time seller
                    </h3>

                    <p className="text-muted-foreground">
                        I am currently a student at NUS. Gunpla building and collecting 
                        is what I do when I'm free. I mostly collect limited kits, especially
                        special coating ones. That's why I almost exclusively sell limited kits.
                    </p>

                    <p className="text-muted-foreground">
                        This website was made for fun during my spare time.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 pt-4 justify-center">
                        <a href="#contact" className="cosmic-button">
                            {" "}
                            Get In Touch
                        </a>
                    </div>
                </div>

                
                <div className="grid grid-cols-1 gap-6">
                    <div className="gradient-border p-6 card-hover">
                        <div className="flex items-start gap-4">
                            <div className="p-3 rounded-full bg-primary/10">
                                <Code className="h-6 w-6 text-primary"/>
                            </div>
                            <div className="text-left">
                                <h4 className="font-semibold text-lg"> University student </h4>
                                <p className="text-muted-foreground"> Pursuing a major in Computer Science </p>
                            </div>
                        </div>
                    </div>
                    <div className="gradient-border p-6 card-hover">
                        <div className="flex items-start gap-4">
                            <div className="p-3 rounded-full bg-primary/10">
                                <Wrench className="h-6 w-6 text-primary"/>
                            </div>
                             <div className="text-left">
                                <h4 className="font-semibold text-lg"> Plamo hobbyist </h4>
                                <p className="text-muted-foreground"> Enjoying the hobby as a casual builder at the expense of my house space </p>
                            </div>
                        </div>
                    </div>
                    <div className="gradient-border p-6 card-hover">
                        <div className="flex items-start gap-4">
                            <div className="p-3 rounded-full bg-primary/10">
                                <ShoppingCart className="h-6 w-6 text-primary"/>
                            </div>
                             <div className="text-left">
                                <h4 className="font-semibold text-lg"> Plamo seller </h4>
                                <p className="text-muted-foreground"> Selling off my backlog and helping you find rare kits at competitive prices </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </section>
}