import { ArrowRight, ExternalLink, Github } from "lucide-react"


const projects = [
    {
        id: 1,
        title: "SaaS Landing Page",
        description: "A Beautiful landing page app using React and Tailwind.",
        image: "/projects/projects1.jpg",
        tags: ["React", "Tailwind", "Supabase"],
        demoUrl: "#",
        githubUrl: "#", 
    },
    {
        id: 2,
        title: "Phenex",
        description: "A personal chatbot",
        image: "/projects/projects2.jpg",
        tags: ["JavaFX", "Java"],
        demoUrl: "#",
        githubUrl: "#", 
    },
    {
        id: 3,
        title: "AuthentiCart",
        description: "An E-commerce platform based on authenticity",
        image: "/projects/projects3.jpg",
        tags: ["React", "Tailwind", "JavaScript", "PostgreSQL"],
        demoUrl: "#",
        githubUrl: "#", 
    },
]

export const ProjectsSection = () => {
    return <section id="projects" className="py-24 px-4 relative">
        <div className="container mx-auto max-w-5xl">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 text-center"> Featured
                <span className="text-primary"> Projects </span>
            </h2>

            <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
                Here are some of my recent projects.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {projects.map((project, key) => (
                    <div key={key} className="group bg-card rounded-lg overflow-hidden shadow-xs card-hover">
                        <div className="h-48 overflow-hidden">
                            <img 
                              src={project.image} 
                              alt={project.title} 
                              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                            />
                        </div>
                        <div className="p-6">
                            <div className="flex flex-wrap gap-2 mb-4">
                                {project.tags.map((tag) => (
                                    <span className="px-2 py-1 text-xs border font-medium rounded-full bg-secondary text-secondary-foreground">
                                        {tag}
                                    </span>
                                ))}
                            </div>

                        <h3 className="text-xl font-semibold mb-2"> {project.title} </h3>
                        <p className="text-muted-foreground text-sm mb-4"> {project.description} </p>
                        <div className="flex justify-between items-center">
                            <div className="flex space-x-3">
                                <a href={project.demoUrl} 
                                   target="_blank"
                                   className="text-foreground/80 hover:text-primary transition-colors duration-300">
                                    <ExternalLink size={20}/>
                                </a>
                                <a href={project.githubUrl} 
                                   target="_blank"
                                   className="text-foreground/80 hover:text-primary transition-colors duration-300">
                                    <Github size={20}/>
                                </a>
                            </div>
                        </div>
                        
                        </div>
                    </div>
                ))}
            </div>

            <div className="text-center mt-12">
                <a className="cosmic-button w-fit flex items-center mx-auto gap-2" href="https://github.com/marchjlim" target="_blank">
                    Check My Github <ArrowRight size={16}/>
                </a>
            </div>
        </div>
    </section>
}